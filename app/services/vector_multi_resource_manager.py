import gc
import os
import threading
import time
import pandas as pd
import faiss
import numpy as np

class VectorMultiResourceManager:
    def __init__(self, settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._is_reloading = False

        self.configs = {
            'text': {
                'index_path': self.settings.FAISS_INDEX_PATH,
                'metadata_path': self.settings.FAISS_METADATA_PATH
            }
        }

        # Hỗ trợ thêm cho Product (Multimodal) nếu có trong settings
        if hasattr(self.settings, 'PRODUCT_FAISS_INDEX_PATH'):
            self.configs['product'] = {
                'index_path': self.settings.PRODUCT_FAISS_INDEX_PATH,
                'metadata_path': self.settings.PRODUCT_FAISS_METADATA_PATH
            }

        # support multi indexes
        # Trạng thái atomic dạng dict: {'text': (index, metadata), 'product': (index, metadata)}
        self._active = {}

    def initialize(self):
        print('[INIT] Loading multi-resources...')
        new_active = {}
        for name, config in self.configs.items():
            try:
                if os.path.exists(config['index_path']) and os.path.exists(config['metadata_path']):
                    index, metadata = self._load(config['index_path'], config['metadata_path'])
                    new_active[name] = (index, metadata)
                    print(f'[INIT] Loaded {name} - {index.ntotal} vectors')
                else:
                    print(f'[WARN] Missing files for {name}. Skipping...')
            except Exception as e:
                print(f'[ERROR] Failed to init {name}: {e}')

        self._active = new_active
        print(f'[INIT] Loaded {len(new_active)} resources')

    def get_resource(self, name):
        # Trả về một tuple (index, metadata) an toàn, đảm bảo tính nguyên tử.
        # Nếu không tồn tại, trả về (None, None)
        return self._active.get(name, (None, None))

    def reload_async(self):
        with self._lock:
            if self._is_reloading:
                print('[RELOAD] Already in progress, skip')
                return

            self._is_reloading = True

        threading.Thread(target=self._reload_pipeline, daemon=True).start()

    def _load(self, index_path, metadata_path):
        print(f'[INFO] Loading FAISS index from {index_path}...')
        index = faiss.read_index(index_path, faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY)

        print(f'[INFO] Loading metadata from {metadata_path}...')
        metadata = pd.read_parquet(metadata_path)

        if index.ntotal != len(metadata):
            raise ValueError(f'Mismatch: index={index.ntotal}, metadata={len(metadata)}')

        return index, metadata

    def _warmup(self, index):
        try:
            dummy = np.random.rand(1, index.d).astype('float32')
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
                print(f'[CLEANUP] Old resources released safely')
            except Exception as e:
                print(f'[CLEANUP ERROR] {e}')

        threading.Thread(target=_cleanup, daemon=True).start()

    def _reload_pipeline(self):
        with self._lock:
            self._is_reloading = True
            start = time.time()
            print('[RELOAD] Start multi-index pipeline')
            try:
                # Copy shallow từ _active hiện tại
                new_active = dict(self._active)
                old_resources_to_cleanup = []

                for name, config in self.configs.items():
                    try:
                        if not os.path.exists(config['index_path']):
                            print(f'[RELOAD] Missing file index {config["index_path"]} for {name}. Skip reloading this component.')
                            continue

                        if not os.path.exists(config['metadata_path']):
                            print(f'[RELOAD] Missing file metadata {config["metadata_path"]} for {name}. Skip reloading this component.')
                            continue

                        new_index, new_metadata = self._load(config['index_path'], config['metadata_path'])
                        # 2. warmup
                        self._warmup(new_index)

                        # Nếu đã có bản cũ đang chạy, đưa vào danh sách chờ xóa
                        if name in new_active:
                            old_resources_to_cleanup.append(new_active[name])

                        new_active[name] = (new_index, new_metadata)
                        print(f'[RELOAD] {name} prepared ({new_index.ntotal} vectors)')
                    except Exception as e:
                        # Partial Reload: Nếu file Product lỗi, file Text vẫn chạy bình thường với bản cũ
                        print(f'[RELOAD] Failed to load {name}: {e}. Retaining old version.')

                # 3. swap atomic (thay thế nguyên cục dictionary trong 1 tick CPU)
                self._active = new_active
                print(f'[RELOAD] Swap success')

                # 4. cleanup (deferred)
                self._cleanup_async(old_resources_to_cleanup)

                # 5. REPORT
                load_time = time.time() - start
                print(f'''
                    [DEPLOY REPORT]
                    load_time: {load_time:.2f}s
                    components_active: {list(self._active.keys())}
                    status: SUCCESS
                    ''')
            except Exception as e:
                print(f'[RELOAD] Failed: {e}')
            finally:
                # Trả lại cờ để cho phép reload lần sau
                with self._lock:
                    self._is_reloading = False
