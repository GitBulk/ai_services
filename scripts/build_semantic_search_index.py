import faiss
import os
import numpy as np
import pandas as pd
from app.services.text_embedding_service import TextEmbeddingService
# from app.core.model_registry import ModelRegistry
from app.core.model_registry import ModelRegistry

BATCH_SIZE = 512
OUTPUT_INDEX = 'data/faiss.index'
OUTPUT_META = 'data/metadata.parquet'

# Ý tưởng cốt lõi
# Embedding + indexing = batch job (offline)
# API chỉ làm: encode query + search
# Mô hình:
#             (Offline job)
# DB  ──→  build_index.py  ──→  FAISS index file
#                          └─→  metadata.json / parquet

#             (Online service)
# FastAPI ──→ load index + metadata ──→ search(query)

OUTPUT_DIR = 'data'
INDEX_PATH = os.path.join(OUTPUT_DIR, 'faiss.index')
META_PATH = os.path.join(OUTPUT_DIR, 'metadata.parquet')

SAMPLE_DATA = [
    {'id': 1, 'text': 'I love coffee', 'user_id': 10},
    {'id': 2, 'text': 'Looking for serious relationship', 'user_id': 11},
    {'id': 3, 'text': 'Just here for fun', 'user_id': 12},
]

def load_data():
    # nên thay bằng load trong DB
    return SAMPLE_DATA

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print('[INFO] Loading embedding model...')
    model_registry = ModelRegistry()
    model_registry.load_models()
    embedding_service = TextEmbeddingService(model=model_registry.get('text_embedding'))
    data = load_data()
    texts = [item['text'] for item in data]
    print('[INFO] Encoding texts...')
    vectors = embedding_service.encode(texts)
    vectors = np.array(vectors).astype('float32')

    print(f'[INFO] Vector shape: {vectors.shape}')

    dim = vectors.shape[1]

    print('[INFO] Building FAISS index...')
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    print('[INFO] Saving index...')
    faiss.write_index(index, INDEX_PATH)

    print('[INFO] Saving metadata...')
    df = pd.DataFrame(SAMPLE_DATA)
    df.to_parquet(META_PATH, index=False)

    print('[SUCCESS] Index built 🚀')

if __name__ == '__main__':
    main()