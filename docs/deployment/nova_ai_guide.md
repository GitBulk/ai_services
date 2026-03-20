# Nova AI – FAISS Deployment Guide

## 1. Mapping Generic → Nova

| Concept            | Nova Implementation                          |
| ------------------ | -------------------------------------------- |
| Immutable Artifact | `faiss_<ts>.index`, `metadata_<ts>.parquet`  |
| Atomic Publish     | `.tmp` → `mv` into `data/releases/`          |
| Symlink Switch     | `data/current.index`, `data/current.parquet` |
| Reload             | `SIGHUP` to FastAPI process                  |
| Healthcheck        | `/health` endpoint                           |
| Rollback           | Re-point symlink + reload                    |

---

## 2. Directory Layout

```
data/
  releases/
    20260320_120001/
      faiss.index
      metadata.parquet
    20260320_130501/
      faiss.index
      metadata.parquet

  current.index -> releases/20260320_130501/faiss.index
  current.parquet -> releases/20260320_130501/metadata.parquet

run/
  nova.pid
```

---

## 3. Deployment Flow

```
[Build Index]
      ↓
[Verify]
      ↓
[Publish (.tmp → mv)]
      ↓
[Switch Symlink]
      ↓
[Send SIGHUP]
      ↓
[Warmup Phase]
      ↓
[Healthcheck]
      ↓
   Success / Fail
      ↓
   Rollback (if needed)
```

---

## 4. Build Step (Offline)

```
make build-index ENV=prod
```

**Output:**

```
build/
  faiss_20260320_130501.index
  metadata_20260320_130501.parquet
```

---

## 5. Verify Step

Basic checks:

* File exists
* Non-zero size
* Matching row count between index & metadata

Example:

```
make verify-index
```

---

## 6. Publish (Atomic)

```
VERSION=20260320_130501

mkdir -p data/releases/$VERSION

cp build/faiss_$VERSION.index data/releases/$VERSION/.tmp.index
cp build/metadata_$VERSION.parquet data/releases/$VERSION/.tmp.parquet

mv data/releases/$VERSION/.tmp.index data/releases/$VERSION/faiss.index
mv data/releases/$VERSION/.tmp.parquet data/releases/$VERSION/metadata.parquet
```

---

## 7. Symlink Switch

```
ln -sfn data/releases/$VERSION/faiss.index data/current.index
ln -sfn data/releases/$VERSION/metadata.parquet data/current.parquet
```

Atomic pointer switch → no partial state.

## 8. Reload (Zero Downtime)

```
kill -HUP $(cat run/nova.pid)
```

**FastAPI behavior:**

* Catch SIGHUP
* Reload FAISS index from `current.*`
* Swap in-memory index

## 8.1. Shadow Load (Parallel Index Loading)

Instead of loading index directly into serving path, use shadow loading.

**Goal:**
- Load new index in parallel
- Avoid blocking live traffic
- Isolate failures before affecting users

**Flow:**
```
current index (serving)
        │
        ├── incoming traffic (unchanged)
        │
        └── shadow load → new_index (in background)
```

**Implementation Concept:**

On SIGHUP:
```
Spawn background task/thread
Load FAISS index into memory → staging_index
Do NOT touch active_index
```

Pseudo-code:
```python
def handle_sighup():
    spawn_background_task(load_new_index)

def load_new_index():
    new_index = load_from_disk("current.index")
    run_warmup(new_index)
    swap_if_ready(new_index)
```

**Key Properties:**
```
Non-blocking
Safe (failures do not impact serving)
Enables zero-downtime for large index (~GBs)
```

## 9. Warmup Phase (Critical for Large Index)
After loading the new index, perform a warmup before switching it into serving.

**Why:**
- FAISS index may be memory-mapped or lazily loaded
- First queries can be slow (cold cache)
- Prevent latency spikes for real users

Warmup Strategy:
1. Run a set of representative queries
2. Touch different parts of the index
3. Ensure memory pages are loaded

Example:
```bash
curl -X POST http://localhost:8000/internal/search \
  -d '{"query": "test query", "top_k": 10}'
```

Run multiple queries (scripted):
```
make warmup-index
```

**FastAPI internal flow:**
- Load new index → new_index
- Run warmup queries on new_index
- If successful → swap:
```
self.index = new_index
```
- If failed → discard new index

**Key Rule:**

Only switch to new index AFTER warmup completes successfully


## 10. Healthcheck

### API

```
GET /health
```

### Example Response

```
{
  "status": "ok",
  "index_version": "20260320_130501",
  "vector_count": 2000000
}
```

### Check Command

```
curl -f http://localhost:8000/health
```

---

## 11. Full Deploy Command

```
make deploy ENV=prod VERSION=20260320_130501
```

**Equivalent Flow:**

```
build → verify → publish → switch → reload → healthcheck
```

---

## 12. Rollback

### Scenario: Healthcheck Failed

```
PREV=20260320_120001

ln -sfn data/releases/$PREV/faiss.index data/current.index
ln -sfn data/releases/$PREV/metadata.parquet data/current.parquet

kill -HUP $(cat run/nova.pid)
```

Reverts instantly to last known-good index.

---

## 13. Failure Scenarios

### Case 1: Corrupted Index

* Verify step should catch
* If missed → healthcheck fails → rollback

### Case 2: Partial Publish

* Prevented by `.tmp → mv`

### Case 3: Reload Crash

* Process exits → supervisor restarts
* Still safe due to immutable artifacts

---

## 14. Notes

* Never modify `current.*` files directly
* Always deploy via versioned releases
* Keep at least last 3 versions for rollback
* Monitor reload time (large FAISS index)

---

## 15. Summary

This deployment model ensures:

* Zero downtime index updates
* Safe rollback
* Deterministic releases

It is optimized for:

* Large FAISS index (~millions of vectors)
* Read-heavy semantic search systems


## 16. Future Implementation
multi-server / rolling deploy (V2 kiến trúc)