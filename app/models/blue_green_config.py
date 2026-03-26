# app/models/recommendation_config.py
from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.active_record_mixin import ActiveRecordMixin
from app.db.session import Base


class BlueGreeConfig(Base, ActiveRecordMixin):
    __tablename__ = "blue_green_configs"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    last_computed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
