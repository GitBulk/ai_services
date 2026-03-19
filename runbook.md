# NOVA AI RUNBOOK - v1.0

## 1. Tổng quan hệ thống
- Offline:
    - build_index → tạo file index + metadata (versioned)

- Online:
    - FastAPI → load index qua symlink (current.index)

- Control:
    - SIGHUP → reload index (không downtime)

## 2. Cấu trúc thư mục
```
├── data/ # Nơi chứa các Model AI (.pth, .bin)
    ├── faiss_20260320_0100.index
    ├── metadata_20260320_0100.parquet
    ├── faiss_20260321_0200.index
    ├── metadata_20260321_0200.parquet
    ├── current.index     -> symlink
    └── current.parquet   -> symlink
```

Service chỉ đọc: - data/current.index - data/current.parquet

## 3. Deploy index mới
```
make deploy
```

Những gì xảy ra bên dưới:
1. Build index mới (timestamp version)
2. Tạo:
   faiss_<VERSION>.index
   metadata_<VERSION>.parquet
3. Update symlink:
   current → version mới
4. Gửi signal SIGHUP
5. Service reload index (không downtime)

Kết quả mong đợi
```
[SUCCESS] Deploy version 20260320_0215 🚀
```

## 4. Kiểm tra version
```
make current
```
Output:
```
current.index -> faiss_20260320_0215.index
current.parquet -> metadata_20260320_0215.parquet
```

## 5. Rollback

Rollback về version cụ thể
```
make rollback VERSION=20260320_0100
```

Rollback gần nhất:
```
make rollback_last
```

Kiểm tra lại:
```
make current
```

## 6. Khi nào cần rollback?
Rollback ngay khi:

❌ Search trả kết quả sai bất thường

❌ API lỗi sau deploy

❌ Index mới build sai data

❌ Metadata mismatch


## 7. Smoke test
```bash
curl -X POST http://localhost:8000/api/v1/search\
-H "Content-Type: application/json"\
-d '{"query": "cheap phone", "top_k": 3}'
```

## 8. Troubleshooting

### ❌ Case 1: API crash sau reload
**Nguyên nhân:**
- File index corrupt
- Metadata mismatch

**Cách xử lý:**
```
make rollback_last
```

### ❌ Case 2: Search trả kết quả rác
**Nguyên nhân:**
- Sai embedding model
- Sai dataset
- Sai normalize

**Cách xử lý:**
```
make rollback_last
```

### ❌ Case 3: Reload không có tác dụng
**Check PID:**
```
ps aux | grep uvicorn
```

**Reload manual:**
```
kill -HUP <pid>
```

### ❌ Case 4: File không tồn tại
```
ls data/
```
👉 đảm bảo có:
```
faiss_<VERSION>.index
metadata_<VERSION>.parquet
```

## 9. Clean
```
make clean_index
```
Rule:
- Giữ lại ít nhất 3 version gần nhất
- Không xóa file đang được symlink

------------------------------------------------------------------------

## 10. Những điều KHÔNG được làm
❌ Không overwrite file
```
cp faiss.index data/faiss.index
```

❌ Không sửa file đang dùng
```
vi data/current.index
```

❌ Không reload khi file chưa sẵn sàng

------------------------------------------------------------------------


## 11. Nguyên tắc an toàn
✅ Immutable files
```
faiss_<VERSION>.index không bao giờ bị sửa
```

✅ Atomic switch
```
ln -sfn → đổi symlink
```

✅ Safe reload
```
load → validate → swap
```

## 12. Insight quan trọng

👉 Hệ thống này dùng pattern:
```
Immutable artifact + pointer switch
```
→ ưu điểm:

✅ Không downtime

✅ Rollback instant

✅ Không race condition

✅ Dễ debug

## 13. Quick cheat sheet
```bash
# Deploy
make deploy

# Check current
make current

# Rollback
make rollback VERSION=xxxx

# Rollback nhanh
make rollback_last

# Clean
make clean_index
```