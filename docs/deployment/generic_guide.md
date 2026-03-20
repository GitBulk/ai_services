# Deployment Guide (Generic)

## Philosophy

A production deployment system should be:

* **Deterministic**: same input → same output
* **Immutable**: artifacts are never modified after build
* **Atomic**: deployment is all-or-nothing
* **Reversible**: fast rollback to a known-good state
* **Observable**: health is measurable at every step

## Core Concepts

### 1. Immutable Artifacts

Build once, deploy many times.

**Rules:**

* Artifacts are versioned (timestamp, git SHA, or semantic version)
* Never mutate artifacts after build
* Store artifacts in a dedicated directory or object storage

**Example:**

```
artifacts/
  app_20260320_120001.tar.gz
  app_20260320_120001.meta.json
```

### 2. Atomic Publish

Deployment must not expose partial state.

**Pattern:**

1. Write to a temporary location
2. Verify integrity
3. Atomically move into place

**Example:**

```
cp artifact.tar.gz releases/.tmp
mv releases/.tmp releases/20260320_120001
```

`mv` on the same filesystem is atomic → guarantees consistency.

### 3. Symlink Switch (Release Pointer)

Use a stable pointer to reference the current version.

**Structure:**

```
releases/
  20260320_120001/
  20260320_130501/
current -> releases/20260320_130501
```

**Deploy:**

```
ln -sfn releases/20260320_130501 current
```

This makes switching versions instant and atomic.

### 4. Reload vs Restart

**Reload (Preferred):**

* Re-read config/data without killing the process
* Zero downtime
* Requires application support (signal or endpoint)

**Restart:**

* Kill and start process
* Simpler but causes downtime

**Guideline:**

* Use reload when state can be safely swapped
* Use restart when process state is complex or unsafe to hot-swap

### 5. Healthcheck

Healthchecks validate system readiness.

**Types:**

* **Liveness**: process is running
* **Readiness**: system can serve traffic correctly

**Example contract:**

```
GET /health
{
  "status": "ok",
  "version": "20260320_130501"
}
```

**Rules:**

* Must be fast (<100ms ideally)
* Must reflect real dependencies (DB, cache, models, etc.)

### 6. Safe Deployment Pipeline

Standard pipeline:

```
build → verify → publish → switch → reload → healthcheck
```

**Step details:**

1. **Build**

   * Produce immutable artifact

2. **Verify**

   * Integrity checks (checksum, schema, size)
   * Optional smoke tests

3. **Publish**

   * Move artifact into releases directory (atomic)

4. **Switch**

   * Update `current` symlink

5. **Reload**

   * Notify application to use new version

6. **Healthcheck**

   * Ensure system is functioning

### 7. Rollback Strategy

Rollback must be:

* Fast
* Deterministic
* Tested

**Mechanism:**

* Keep previous releases
* Re-point symlink
* Reload

**Example:**

```
ln -sfn releases/20260320_120001 current
kill -HUP $(cat app.pid)
```

### 8. Idempotency

Deployment commands should be safe to run multiple times.

**Practices:**

* Avoid destructive operations
* Use checks before overwrite
* Prefer `ln -sfn`, `mv`, etc.

### 9. Versioning Strategy

Choose one:

* Timestamp (simple, sortable)
* Git SHA (traceable)
* Semantic version (human-friendly)

**Recommendation:**
Combine:

```
20260320_130501_ab12cd3
```

### 10. Directory Layout (Reference)

```
project/
  releases/
    <version>/
  current -> releases/<version>
  shared/
  logs/
  run/
    app.pid
```


## Deployment Checklist

* [ ] Artifact built and versioned
* [ ] Artifact verified
* [ ] Published atomically
* [ ] Symlink switched
* [ ] Application reloaded/restarted
* [ ] Healthcheck passed
* [ ] Rollback path confirmed


## Anti-Patterns

Avoid:

* Editing files in-place inside `current`
* Non-atomic copy operations
* Restarting without health validation
* Deleting previous releases immediately
* Coupling build and deploy environments tightly



## Summary

This guide defines a minimal, production-ready deployment model based on:

* Immutable artifacts
* Atomic operations
* Symlink-based version switching
* Explicit health validation

It is intentionally generic and can be applied to:

* Web services
* ML systems
* Batch pipelines
* Search infrastructure

The next layer should adapt these principles to a specific system.
