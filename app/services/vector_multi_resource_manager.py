import gc
import os
import threading
import time

import faiss
import numpy as np
import pandas as pd


class VectorMultiResourceManager:
    def __init__(self, settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._is_reloading = False

        self.configs = {
            "text": {
                "index_path": self.settings.FAISS_INDEX_PATH,
                "metadata_path": self.settings.FAISS_METADATA_PATH,
            }
        }

        # Hỗ trợ thêm cho Product (Multimodal) nếu có trong settings
        if hasattr(self.settings, "PRODUCT_FAISS_INDEX_PATH"):
            self.configs["product"] = {
                "index_path": self.settings.PRODUCT_FAISS_INDEX_PATH,
                "metadata_path": self.settings.PRODUCT_FAISS_METADATA_PATH,
            }

        # support multi indexes
        # Trạng thái atomic dạng dict: {'text': (index, metadata), 'product': (index, metadata)}
        self._active = {}

    def initialize(self):
        print("[INIT] Loading multi-resources...")
        new_active = {}
        for resource_name, config in self.configs.items():
            try:
                if os.path.exists(config["index_path"]) and os.path.exists(config["metadata_path"]):
                    index, metadata = self._load(config["index_path"], config["metadata_path"])
                    new_active[resource_name] = (index, metadata)
                    print(f"[INIT] Loaded {resource_name} - {index.ntotal} vectors")
                else:
                    print(f"[WARN] Missing files for {resource_name}. Skipping...")
            except Exception as e:
                print(f"[ERROR] Failed to init {resource_name}: {e}")

        self._active = new_active
        print(f"[INIT] Loaded {len(new_active)} resources")

    def get_resource(self, resource_name):
        # Trả về một tuple (index, metadata) an toàn, đảm bảo tính nguyên tử.
        # Nếu không tồn tại, trả về (None, None)
        return self._active.get(resource_name, (None, None))

    def reload_async(self):
        with self._lock:
            if self._is_reloading:
                print("[RELOAD] Already in progress, skip")
                return

            self._is_reloading = True

        threading.Thread(target=self._reload_pipeline, daemon=True).start()

    def _load(self, index_path, metadata_path):
        print(f"[INFO] Loading FAISS index from {index_path}...")
        index = faiss.read_index(index_path, faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY)

        print(f"[INFO] Loading metadata from {metadata_path}...")
        metadata = pd.read_parquet(metadata_path)

        if index.ntotal != len(metadata):
            raise ValueError(f"Mismatch: index={index.ntotal}, metadata={len(metadata)}")

        return index, metadata

    def _warmup(self, index):
        try:
            dummy = np.random.rand(1, index.d).astype("float32")
            index.search(dummy, 5)
        except Exception:
            # warmup best-effort
            pass

    def _cleanup_async(self, old_resources_list):
        if not old_resources_list:
            return

        def _cleanup():
            try:
                # grace period
                time.sleep(5)
                old_resources_list.clear()
                gc.collect()
                print("[CLEANUP] Old resources released safely")
            except Exception as e:
                print(f"[CLEANUP ERROR] {e}")

        threading.Thread(target=_cleanup, daemon=True).start()

    def _reload_pipeline(self):
        with self._lock:
            self._is_reloading = True
            start = time.time()
            print("[RELOAD] Start multi-index pipeline")
            try:
                # Copy shallow từ _active hiện tại
                new_active = dict(self._active)
                old_resources_to_cleanup = []

                for resource_name, config in self.configs.items():
                    try:
                        if not os.path.exists(config["index_path"]):
                            print(
                                f"[RELOAD] Missing file index {config['index_path']} for {resource_name}. Skip reloading this component."
                            )
                            continue

                        if not os.path.exists(config["metadata_path"]):
                            print(
                                f"[RELOAD] Missing file metadata {config['metadata_path']} for {resource_name}. Skip reloading this component."
                            )
                            continue

                        new_index, new_metadata = self._load(
                            config["index_path"], config["metadata_path"]
                        )
                        # 2. warmup
                        self._warmup(new_index)

                        # Nếu đã có bản cũ đang chạy, đưa vào danh sách chờ xóa
                        if resource_name in new_active:
                            old_resources_to_cleanup.append(new_active[resource_name])

                        new_active[resource_name] = (new_index, new_metadata)
                        print(f"[RELOAD] {resource_name} prepared ({new_index.ntotal} vectors)")
                    except Exception as e:
                        # Partial Reload: Nếu file Product lỗi, file Text vẫn chạy bình thường với bản cũ
                        print(
                            f"[RELOAD] Failed to load {resource_name}: {e}. Retaining old version."
                        )

                # 3. swap atomic (thay thế nguyên cục dictionary trong 1 tick CPU)
                self._active = new_active
                print("[RELOAD] Swap success")

                # 4. cleanup (deferred)
                self._cleanup_async(old_resources_to_cleanup)

                # 5. REPORT
                load_time = time.time() - start
                print(f"""
                    [DEPLOY REPORT]
                    load_time: {load_time:.2f}s
                    components_active: {list(self._active.keys())}
                    status: SUCCESS
                    """)
            except Exception as e:
                print(f"[RELOAD] Failed: {e}")
            finally:
                # Trả lại cờ để cho phép reload lần sau
                with self._lock:
                    self._is_reloading = False

    def inject_resource(self, resource_name: str, index: faiss.Index, metadata: pd.DataFrame):
        """
        Tiêm (inject) trực tiếp FAISS Index và Metadata vào memory mà không cần đọc từ file đĩa.
        Hàm này hỗ trợ nạp dữ liệu động hoặc dùng trong Unit Test. Đảm bảo tính Thread-safe
        và sẽ tự động dọn dẹp (cleanup) các resource cũ nếu bị ghi đè.

        Args:
            name (str): Tên của resource muốn tiêm vào (vd: 'text', 'product', 'test_mock').
            index (faiss.Index): Đối tượng FAISS Index đã được nạp sẵn vector trên RAM.
            metadata (pd.DataFrame): Pandas DataFrame chứa dữ liệu tương ứng với Index.
        Raises:
            ValueError: Nếu số lượng vector trong `index` không khớp với số dòng của `metadata`.

        Examples:
            Tạo một index giả trên RAM và tiêm vào hệ thống để test:

            >>> import faiss
            >>> import numpy as np
            >>> import pandas as pd
            >>>
            >>> fake_index = faiss.IndexFlatL2(512)
            >>> fake_index.add(np.random.rand(2, 512).astype('float32'))
            >>>
            >>> fake_metadata = pd.DataFrame([
            ...     {'id': 1, 'name': 'Giày Test 1'},
            ...     {'id': 2, 'name': 'Giày Test 2'}
            ... ])
            >>>
            >>> manager = VectorMultiResourceManager(settings)
            >>> manager.inject_resource('test_mock', fake_index, fake_metadata)

        Returns:
            None
        """
        print(f'[INJECT] Injecting resource "{resource_name}"...')
        if index.ntotal != len(metadata):
            raise ValueError(
                f"Inject failed! Mismatch: index={index.ntotal}, metadata={len(metadata)}"
            )

        # Warmup (Làm nóng Index mới)
        self._warmup(index)

        # Thread-safe Swap (Tráo đổi an toàn)
        # Copy danh sách hiện tại để không ảnh hưởng đến các request đang đọc
        new_active = dict(self._active)
        old_resource = new_active.get(resource_name)

        # Cập nhật bản ghi mới
        new_active[resource_name](index, metadata)

        # Đổi tham chiếu atomic trong 1 tick CPU
        self._active = new_active

        # 4. Dọn dẹp bản cũ (nếu trước đó đã có resource tên này)
        if old_resource:
            self._cleanup_async([old_resource])

        print(f'[INJECT] Success! "{resource_name}" now has {index.ntotal} vectors.')
