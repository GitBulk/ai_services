# 🚀 Nova AI – Simple Deployment Guide, Makefile usage

# Updated

Please read nova_ai_guide.md for more details about deployment guilde

## 1. Overview

This document describes how to deploy the **FAISS-based semantic search system** for Nova AI.

## 2. Artifacts

Each deployment generates:
```
faiss_<version>.index
metadata_<version>.parquet
```

These are:

- Immutable
- Versioned
- Stored in `data/`

---

## 3. Runtime Files

Service loads:
```
data/current.index
data/current.parquet
```

These are symlinks pointing to versioned files.

## 4. Deployment Flow
1. Build index (.tmp)
2. Verify files
3. Publish (mv .tmp → final)
4. Update symlink
5. Reload service
6. Healthcheck
7. Auto rollback if failed


## 5. Commands (Makefile)

### Run service

```
make run ENV=staging
```

### Deploy (safe)
```
make safe_deploy ENV=staging
```

### Reload
```
make reload ENV=staging
```

### Rollback
```
make rollback VERSION=<version> ENV=staging
```

### Rollback last
```
make rollback_last ENV=staging
```

### Check current version
```
make current
```
## 6. Safe Deploy Pipeline

```
build_index → verify → publish → link → reload → healthcheck
```

## 7. Healthcheck

Example request:
```
POST /api/v1/search
{
"query": "cheap phone",
"top_k": 1
}
```
Expected:

- Response contains `result`
- Score is reasonable
- Data is relevant

## 8. Reload Mechanism

Uses:
```
kill -HUP <pid>
```

PID stored in: `nova.pid`


## 9. Rollback Strategy

Rollback is instant:
```
ln -sfn old_version → current
kill -HUP
```
## 10. Failure Handling

### Case: Deploy fails

→ Auto rollback triggered

---

### Case: API returns invalid data

→ Rollback immediately

---

### Case: Index corrupted

→ Verify step prevents publish


## 11. Environment

Config files:
```
.env.dev
.env.staging
.env.prod
```

Loaded via Settings.

## 12. Data Source

Current dataset:

- Tatoeba sentences
- ~2M records

## 13. Model

Embedding model: `SentenceTransformer (multilingual MiniLM)`

## 14. FAISS Setup

- Index: `IndexFlatIP`
- Similarity: cosine (via L2 normalization)

## 15. Future Improvements

- Multi-server deploy
- Rolling update
- Distributed search
- Incremental indexing

## 16. Summary

Nova AI deploy is: Versioned FAISS index
```
Symlink switch

Signal reload

Safe rollback
```