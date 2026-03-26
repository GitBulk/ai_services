from sqlalchemy import inspect
from sqlalchemy.orm import Session


class ActiveRecordMixin:
    @classmethod
    def find_by(cls, db: Session, **kwargs):
        return db.query(cls).filter_by(**kwargs).first()

    @classmethod
    def all(cls, db: Session):
        return db.query(cls).all()

    @classmethod
    def where(cls, db: Session, **kwargs):
        return db.query(cls).filter_by(**kwargs)

    def __repr__(self) -> str:
        # tự động lấy tên class
        class_name = self.__class__.__name__
        inst = inspect(self)

        fields = []
        for column in inst.mapper.column_attrs:
            key = column.key
            value = getattr(self, key)
            fields.append(f"{key}={value!r}")

        return f"<{class_name}({', '.join(fields)})>"
