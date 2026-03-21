import gc
import os
import threading
import time
import pandas as pd
import faiss
import numpy as np

class VectorResourceManager:
    def __init__(self, index_path, metadata_path):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._lock = threading.Lock()
        self._is_reloading = False
        # atomic state (index, metadata)
        self._active = (None, None)

    def initialize(self):
        print('[INIT] Loading resources...')
        index, metadata = self._load()
        self._active = (index, metadata)
        print(f'[INIT] Loaded {index.ntotal} vectors')

    @property
    def resources(self):
        return self._active

    def reload_async(self):
        if self._is_reloading:
            print('[RELOAD] Already in progress, skip')
            return

        threading.Thread(target=self._reload_pipeline, daemon=True).start()

    def _load(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(self.index_path)

        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(self.metadata_path)

        print('[INFO] Loading FAISS index...')
        index = faiss.read_index(self.index_path, faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY)
        print('[INFO] Loading metadata...')
        metadata = pd.read_parquet(self.metadata_path)

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

    def _cleanup_async(self, old_index, old_metadata):
        def _cleanup():
            try:
                # grace period
                time.sleep(5)
                del old_index
                del old_metadata
                gc.collect()
                print(f'[CLEANUP] Old resources released')
            except Exception as e:
                print(f'[CLEANUP ERROR] {e}')

        threading.Thread(target=_cleanup, daemon=True).start()

    def _reload_pipeline(self):
        with self._lock:
            self._is_reloading = True
            start = time.time()
            print('[RELOAD] Start')
            try:
                # 1. shadow load
                new_index, new_metadata = self._load()
                load_time = time.time() - start

                # 2. warmup
                self._warmup(new_index)

                # 3. swap atomic
                old_index, old_metadata = self._active
                self._active = (new_index, new_metadata)

                print(f'[RELOAD] Swap success ({new_index.ntotal}) vectors')

                # 4. cleanup (deferred)
                self._cleanup_async(old_index, old_metadata)

                # 5. REPORT
                print(f'''
                    [DEPLOY REPORT]
                    load_time: {load_time:.2f}s
                    status: SUCCESS
                    ''')
            except Exception as e:
                print(f'[RELOAD] Failed: {e}')
            finally:
                self._is_reloading = False
