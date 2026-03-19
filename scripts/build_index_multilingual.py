# scripts/build_index_multilingual.py
import os
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from app.core.settings import settings  # reuse Settings
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--version', required=True)
args = parser.parse_args()

VERSION = args.version

# ---------------- SETTINGS ----------------
OUTPUT_DIR = 'data'
INDEX_PATH = os.path.join(OUTPUT_DIR, f'faiss_{VERSION}.index')
META_PATH = os.path.join(OUTPUT_DIR, f'metadata_{VERSION}.parquet')
BATCH_SIZE = 256  # nhỏ hơn để progress update nhanh, Ctrl-C dễ

# Dataset: Tatoeba eng_sentences.tsv
DATA_PATH = 'data/eng_sentences.tsv.bz2'

# ---------------- LOAD DATA ----------------
print("[INFO] Loading dataset...")
df = pd.read_csv(DATA_PATH, sep='\t', header=None, names=['id', 'text'])
texts = df['text'].tolist()
ids = df['id'].tolist()
print(f"[INFO] Total sentences: {len(texts)}")

# ---------------- LOAD MODEL ----------------
print(f"[INFO] Loading multilingual embedding model on {settings.DEVICE} ...")
model = SentenceTransformer(
    'paraphrase-multilingual-MiniLM-L12-v2',
    device=settings.DEVICE
)

# ---------------- ENCODING ----------------
vectors = []
total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"[INFO] Encoding {len(texts)} texts...")
vectors = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True, convert_to_numpy=True)
vectors = vectors.astype('float32')

# Normalize for cosine similarity
faiss.normalize_L2(vectors)
print(f"[INFO] Vectors shape: {vectors.shape}")

# ---------------- BUILD FAISS INDEX ----------------
dim = vectors.shape[1]
print("[INFO] Building FAISS IndexFlatIP (cosine similarity)...")
index = faiss.IndexFlatIP(dim)
index.add(vectors)
print(f"[INFO] Number of vectors in index: {index.ntotal}")

# ---------------- SAVE INDEX & METADATA ----------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
print("[INFO] Saving FAISS index...")
# faiss.write_index(index, INDEX_PATH)
faiss.write_index(index, INDEX_PATH, '.tmp')

print("[INFO] Saving metadata...")
# df.to_parquet(META_PATH, index=False)
df.to_parquet(META_PATH + '.tmp', index=False)

print("[SUCCESS] Multilingual FAISS index built 🚀")