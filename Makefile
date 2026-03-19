# ================================
# CONFIG
# ================================
PYTHON = ./env_nova/bin/python
UVICORN = ./env_nova/bin/uvicorn
APP_MODULE = app.main:app
# folder data trong project
DATA_DIR = data

# VERSION (cho phép override từ CLI)
VERSION ?= $(shell date +%Y%m%d_%H%M%S)
INDEX_FILE = faiss_$(VERSION).index
META_FILE = metadata_$(VERSION).parquet

# PID (dev mode)
PID := $(shell pgrep -f "uvicorn")


# .PHONY: run install freeze clean test
.PHONY: run install freeze clean test \
        build_index publish link reload deploy current

# Lệnh chạy server (Development)
run:
	$(UVICORN) $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

# Lệnh cài đặt thư viện từ requirements.txt
install:
	$(PYTHON) -m pip install -r requirements.txt

# Lệnh chốt sổ thư viện requirements.txt tương tự Gemfile.lock
freeze:
	$(PYTHON) -m pip freeze > requirements.txt

# Lệnh chạy test
test:
	$(PYTHON) -m pytest

# Lệnh dọn dẹp các file rác của Python (__pycache__)
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ================================
# BUILD INDEX (MULTILINGUAL)
# ================================

semantic_index:
	$(PYTHON) -m scripts.build_semantic_search_index

build_index:
	@echo "[INFO] Building FAISS index version $(VERSION)..."
	$(PYTHON) scripts/build_index_multilingual.py --version $(VERSION)


# ================================
# ATOMIC PUBLISH (SAFE)
# ================================
publish:
	@echo "[INFO] Publishing index (atomic)..."
	mv $(DATA_DIR)/$(INDEX_FILE).tmp $(DATA_DIR)/$(INDEX_FILE)
	mv $(DATA_DIR)/$(META_FILE).tmp $(DATA_DIR)/$(META_FILE)

# ================================
# SYMLINK SWITCH
# ================================
link:
	@echo "[INFO] Updating symlink..."
	ln -sfn $(INDEX_FILE) $(DATA_DIR)/current.index
	ln -sfn $(META_FILE) $(DATA_DIR)/current.parquet

# ================================
# RELOAD SERVICE
# ================================
reload:
	@echo "[INFO] Reloading service (SIGHUP)..."
	kill -HUP $(PID)

# ================================
# FULL PIPELINE
# ================================
deploy: build_index link reload
	@echo "[SUCCESS] Deploy version $(VERSION) 🚀"

# ================================
# DEBUG
# ================================
current:
	@echo "[INFO] Current active index:"
	ls -l $(DATA_DIR)/current.index
	ls -l $(DATA_DIR)/current.parquet

# ================================
# ROLLBACK
# Usage:
# make rollback VERSION=20260319_0200
# ================================
rollback:
	@if [ -z "$(VERSION)" ]; then \
		echo "Please provide VERSION=..."; exit 1; \
	fi
	@echo "[INFO] Rolling back to version $(VERSION)..."
	ln -sfn faiss_$(VERSION).index $(DATA_DIR)/current.index
	ln -sfn metadata_$(VERSION).parquet $(DATA_DIR)/current.parquet
	kill -HUP $(PID)
	@echo "[SUCCESS] Rolled back to $(VERSION) 🚀"

# ================================
# Lấy version trước đó để rollback
# Usage:
# make rollback_last
# ================================
rollback_last:
	@echo "[INFO] Rolling back to previous version..."

	PREV_INDEX=$$(ls -t $(DATA_DIR)/faiss_*.index | sed -n '2p'); \
	PREV_META=$$(ls -t $(DATA_DIR)/metadata_*.parquet | sed -n '2p'); \

	if [ -z "$$PREV_INDEX" ]; then \
		echo "No previous version found"; exit 1; \
	fi; \

	ln -sfn $$(basename $$PREV_INDEX) $(DATA_DIR)/current.index; \
	ln -sfn $$(basename $$PREV_META) $(DATA_DIR)/current.parquet; \
	kill -HUP $(PID); \

	echo "[SUCCESS] Rolled back to previous version 🚀"