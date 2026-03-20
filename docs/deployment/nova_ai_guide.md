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

---

## 8. Reload (Zero Downtime)

```
kill -HUP $(cat run/nova.pid)
```

**FastAPI behavior:**

* Catch SIGHUP
* Reload FAISS index from `current.*`
* Swap in-memory index

---

## 9. Healthcheck

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

## 10. Full Deploy Command

```
make deploy ENV=prod VERSION=20260320_130501
```

**Equivalent Flow:**

```
build → verify → publish → switch → reload → healthcheck
```

---

## 11. Rollback

### Scenario: Healthcheck Failed

```
PREV=20260320_120001

ln -sfn data/releases/$PREV/faiss.index data/current.index
ln -sfn data/releases/$PREV/metadata.parquet data/current.parquet

kill -HUP $(cat run/nova.pid)
```

Reverts instantly to last known-good index.

---

## 12. Failure Scenarios

### Case 1: Corrupted Index

* Verify step should catch
* If missed → healthcheck fails → rollback

### Case 2: Partial Publish

* Prevented by `.tmp → mv`

### Case 3: Reload Crash

* Process exits → supervisor restarts
* Still safe due to immutable artifacts

---

## 13. Notes

* Never modify `current.*` files directly
* Always deploy via versioned releases
* Keep at least last 3 versions for rollback
* Monitor reload time (large FAISS index)

---

## 14. Summary

This deployment model ensures:

* Zero downtime index updates
* Safe rollback
* Deterministic releases

It is optimized for:

* Large FAISS index (~millions of vectors)
* Read-heavy semantic search systems


## 15. Future Implementation
multi-server / rolling deploy (V2 kiến trúc)