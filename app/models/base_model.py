from rich import inspect as rich_inspect
from tortoise.models import Model

from app.models.ordered_query_set import OrderedQuerySet


class BaseModel(Model):
    @classmethod
    def start_query(cls) -> OrderedQuerySet:
        return OrderedQuerySet(cls)

    @property
    def to_dict(self):
        return dict(self)

    def pp(self, methods=False):
        """
        Dùng rich để in ra object cực đẹp trong console
        methods=True nếu muốn soi cả các hàm của Tortoise
        """
        rich_inspect(self, title=f"<{self.__class__.__name__} ID: {self.id}>", methods=methods)
        return self  # Để có thể gõ p[0].pretty().some_method()

    class Meta:
        abstract = True
