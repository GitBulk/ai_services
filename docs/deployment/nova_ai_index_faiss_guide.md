# Nova AI – INDEX + FAISS Deployment Guide

## 0. Deployment Pipeline (Executive Summary)
```
        ┌───────────────┐
        │   Build Index │
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │    Verify     │
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │    Publish    │  (.tmp → mv)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │  Symlink      │  (current → new version)
        │   Switch      │
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │    Reload     │  (SIGHUP)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │ Shadow Load   │  (background)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │   Warmup      │  (preload + test queries)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │  Swap Guard   │  (validate before promote)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │   Promote     │  (candidate → active)
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │ Healthcheck   │
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │ Deploy Report │
        └──────┬────────┘
               ↓
        ┌───────────────┐
        │   SUCCESS     │
        │   or ABORT    │
        └───────────────┘
```
Failure at any stage before Promote → NO IMPACT (old index still serving)

Failure after Promote → Rollback via symlink + reload


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
Load FAISS index into memory → candidate_index
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

## 8.2. Warmup Phase (Critical for Large Index)
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


## 8.3 Swap Guard (Safety Gate Before Activation)

Before promoting candidate_index → active_index, enforce a strict validation layer.

**Goal:**
- Prevent bad index from going live
- Detect silent corruption or partial mismatch

**Guard Conditions:**
1. Vector Count Match
    - candidate_index.ntotal == metadata_row_count

2. Load Time Threshold
    - Load time within acceptable bound (e.g. < 60s)
    - Detect abnormal slow loads (disk / corruption issues)

3. Warmup Success
    - All warmup queries executed without error
    - Latency within acceptable range

4. Basic Query Sanity Check (Optional but Recommended)
    - Known query returns expected number of results

Pseudo-code:
```python
def swap_if_ready(new_index):
    if not guard_passed(new_index):
        log("[DEPLOY] Swap rejected")
        return

    self.index = new_index
    log("[DEPLOY] Swap success")


def guard_passed(index):
    return (
        index.ntotal == expected_count
        and load_time < MAX_LOAD_TIME
        and warmup_ok
    )
```

Failure Behavior:
```
Reject swap
Keep serving old index
Log error for investigation
No rollback needed (system never switched)
```

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
* Should have report log

After each deployment attempt (success or failure), emit a structured deploy report.

**Goal:**
- Make deployments observable
- Enable fast debugging
- Provide audit trail for each version

Example Log:
```
[DEPLOY REPORT]
version: 20260320_130501
vector_count: 2000000
load_time: 12.3s
warmup_avg_latency: 18ms
warmup_status: OK
swap_guard: PASSED
final_status: SUCCESS
```
On Failure:
```
[DEPLOY REPORT]
version: 20260320_130501
vector_count: 1998000
load_time: 85.2s
warmup_status: FAILED
swap_guard: REJECTED
final_status: ABORTED
```
Where to Log:
- Application logs (stdout / file)
- Optional: send to monitoring system (ELK, Datadog, etc.)

When to Emit:
- After warmup
- After swap decision (pass/fail)

Key Fields:
```
version
vector_count
load_time
warmup metrics
guard result
final status
```

## 15. Summary

This deployment model ensures:

* Zero downtime index updates
* Safe rollback
* Deterministic releases

It is optimized for:

* Large FAISS index (~millions of vectors)
* Read-heavy semantic search systems


## 15. Future Implementation
multi-server / rolling deploy (V2 kiến trúc)