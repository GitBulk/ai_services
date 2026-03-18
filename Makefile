# Biến số để dễ quản lý
PYTHON = ./env_nova/bin/python
UVICORN = ./env_nova/bin/uvicorn
APP_MODULE = app.main:app

.PHONY: run install freeze clean test

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

semantic_index:
	$(PYTHON) -m scripts.build_semantic_search_index

multi_language_index:
	$(PYTHON) -m scripts.build_index_multilingual

# Lệnh dọn dẹp các file rác của Python (__pycache__)
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete