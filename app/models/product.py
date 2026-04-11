from tortoise import fields
from tortoise.contrib.postgres.indexes import GinIndex

from app.models.base_model import BaseModel


class Product(BaseModel):
    id = fields.IntField(pk=True)
    image_path = fields.CharField(max_length=255, null=True)
    gender = fields.CharField(max_length=20, null=True)
    master_category = fields.CharField(max_length=100, null=True)
    sub_category = fields.CharField(max_length=100, null=True)
    article_type = fields.CharField(max_length=100, null=True)
    base_colour = fields.CharField(max_length=50, null=True)
    season = fields.CharField(max_length=20, null=True)
    year = fields.SmallIntField(null=True)
    usage = fields.CharField(max_length=50, null=True)
    product_display_name = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=12, decimal_places=2, null=True)
    brand = fields.CharField(max_length=100, null=True)
    text_for_ai = fields.TextField(null=True)

    # Cột search_vector là cột 'Read Only' phía App vì DB tự tính toán
    # Tortoise không có field TSVector nên ta dùng TextField và đánh dấu null=True
    search_vector = fields.TextField(null=True, pk=False, generated=True)

    class Meta:
        table = "products"
        # Index phức hợp để search brand + price cho nhanh
        # indexes = [("brand", "price")]
        indexes = [
            GinIndex(fields=["search_vector"], name="idx_products_search_vector"),
        ]
