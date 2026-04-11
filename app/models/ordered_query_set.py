from tortoise.expressions import RawSQL
from tortoise.queryset import QuerySet


class OrderedQuerySet(QuerySet):
    def filter_in_order(self, ids: list):
        if not ids:
            return self.filter(id__isnull=True)  # Trả về query rỗng an toàn

        # Ép kiểu để tránh SQL Injection
        ids_int = [int(i) for i in ids]
        ids_str = ",".join(map(str, ids_int))

        # Inject array_position của Postgres
        return (
            self.filter(id__in=ids_int)
            .annotate(_order=RawSQL(f"array_position(ARRAY[{ids_str}], id)"))
            .order_by("_order")
        )
