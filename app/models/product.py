from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.active_record_mixin import ActiveRecordMixin
from app.db.session import Base


class Product(Base, ActiveRecordMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
