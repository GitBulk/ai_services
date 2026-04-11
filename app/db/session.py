from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# pool_pre_ping=True rất quan trọng cho Postgres 9.5 để tự động kết nối lại nếu bị ngắt (stale connections)
if settings.is_development:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=True,
        isolation_level="AUTOCOMMIT",  # Mỗi lệnh SQL sẽ là một transaction riêng biệt và tự đóng
    )
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Định nghĩa Base class cho các Models
BaseModel = declarative_base()


def get_db():
    # Tạo một Database Session mới cho mỗi Request và đảm bảo nó được đóng sau khi xong.
    # Cách dùng trong FastAPI: db: Session = Depends(get_db)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
