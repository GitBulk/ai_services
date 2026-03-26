# ================================
# CONFIG
# ================================
# PYTHON = ./env_nova/bin/python
# UVICORN = ./env_nova/bin/uvicorn
PYTHON =  python
UVICORN = uvicorn

APP_MODULE = app.main:app
# folder data trong project
DATA_DIR = data
PID_FILE = tmp/pids/nova.pid

# ENV (default: dev)
ENV ?= dev
export ENV

# VERSION (cho index)
INDEX_VERSION ?= $(shell date +%Y%m%d_%H%M%S)
INDEX_FILE = faiss_$(INDEX_VERSION).index
META_FILE = metadata_$(INDEX_VERSION).parquet

PRODUCT_INDEX_FILE = faiss_products_$(INDEX_VERSION).index
PRODUCT_META_FILE = metadata_products_$(INDEX_VERSION).parquet

.PHONY: run stop restart reload \
        install freeze test clean \
        build_index deploy link current rollback rollback_last clean_index

define CHECK_PID
	if [ ! -f $(PID_FILE) ]; then \
		echo "❌ PID file not found"; exit 1; \
	fi; \
	PID=$$(cat $(PID_FILE)); \
	if ! kill -0 $$PID 2>/dev/null; then \
		echo "❌ Process $$PID not running"; exit 1; \
	fi;
endef

# ================================
# DEV / RUN
# ================================
run:
ifeq ($(ENV),dev)
	@echo "[INFO] Running in DEV mode (ENV=$(ENV))..."
	$(UVICORN) $(APP_MODULE) --reload --host 0.0.0.0 --port 8000
else
	@echo "[INFO] Running in $(ENV) mode..."
	@mkdir -p tmp/pids
	$(UVICORN) $(APP_MODULE) --host 0.0.0.0 --port 8000 & echo $$! > $(PID_FILE)
endif


stop:
ifeq ($(ENV),dev)
	@echo "⚠️ Stop not supported in dev"
else
	@echo "[INFO] Stopping service..."
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID && rm -f $(PID_FILE); \
			echo "[SUCCESS] Stopped $$PID"; \
		else \
			echo "⚠️ Process not running"; \
			rm -f $(PID_FILE); \
		fi \
	else \
		echo "⚠️ No PID file found"; \
	fi
endif


restart: stop run

reload:
ifeq ($(ENV),dev)
	@echo "⚠️ Reload not supported in dev (--reload mode)"
else
	@echo "[INFO] Reloading service..."
	@$(CHECK_PID)
	kill -HUP $$(cat $(PID_FILE))
	@echo "[SUCCESS] Reload signal sent 🚀"
endif


# ================================
# PACKAGE / TEST
# ================================

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
# BUILD FAISS INDEX
# ================================

semantic_index:
	$(PYTHON) -m scripts.build_semantic_search_index

build_index:
	@echo "[INFO] Building index VERSION=$(INDEX_VERSION), ENV=$(ENV)..."
	$(PYTHON) scripts/build_index_multilingual.py --version $(INDEX_VERSION)

build_test_index:
	@echo "[INFO] Building test index VERSION=$(INDEX_VERSION)"
	$(PYTHON) scripts/build_index_multilingual.py --version $(INDEX_VERSION) --limit 1000

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
	@echo "[INFO] Switching symlink to VERSION=$(INDEX_VERSION)..."
	ln -sfn $(INDEX_FILE) $(DATA_DIR)/current.index
	ln -sfn $(META_FILE) $(DATA_DIR)/current.parquet

symlink_product_index:
	@echo "[INFO] Switching symlink to VERSION=$(INDEX_VERSION)..."
	ln -sfn $(PRODUCT_INDEX_FILE) $(DATA_DIR)/products_current.index
	ln -sfn $(PRODUCT_META_FILE) $(DATA_DIR)/products_current.parquet


# ================================
# DEPLOY (1 SERVER)
# 1. build_index.py → tạo file.tmp
# 2. publish → mv tmp → final (atomic)
# 3. link → switch symlink
# 4. reload → load index mới
# Tức là:
# faiss_123.tmp   (đang build)
#         ↓
# mv (atomic)
#         ↓
# faiss_123.index  (safe)
#         ↓
# ln -sfn → current.index
#         ↓
# kill -HUP
# ================================

deploy:
	build_index publish link reload
	@echo "[SUCCESS] Deploy VERSION=$(INDEX_VERSION) 🚀"

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
	@if [ -z "$(INDEX_VERSION)" ]; then \
		echo "Please provide VERSION=..."; exit 1; \
	fi
	@echo "[INFO] Rolling back to VERSION=$(INDEX_VERSION)..."
	ln -sfn faiss_$(INDEX_VERSION).index $(DATA_DIR)/current.index
	ln -sfn metadata_$(INDEX_VERSION).parquet $(DATA_DIR)/current.parquet
	@$(CHECK_PID)
	kill -HUP $$(cat $(PID_FILE))
	@echo "[SUCCESS] Rolled back to $(INDEX_VERSION) 🚀"

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
	$(MAKE) reload; \

	echo "[SUCCESS] Rolled back to previous version 🚀"

# ================================
# CLEAN OLD INDEX
# ================================

clean_index:
	@echo "[INFO] Cleaning old index files..."
	ls -t $(DATA_DIR)/faiss_*.index | tail -n +4 | xargs rm -f
	ls -t $(DATA_DIR)/metadata_*.parquet | tail -n +4 | xargs rm -f

console:
	$(PYTHON) scripts/console.py