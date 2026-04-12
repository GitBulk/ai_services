from tortoise import fields, migrations
from tortoise.contrib.postgres.indexes import GinIndex
from tortoise.migrations import operations as ops


class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name="Product",
            fields=[
                ("id", fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ("image_path", fields.CharField(null=True, max_length=255)),
                ("gender", fields.CharField(null=True, max_length=20)),
                ("master_category", fields.CharField(null=True, max_length=100)),
                ("sub_category", fields.CharField(null=True, max_length=100)),
                ("article_type", fields.CharField(null=True, max_length=100)),
                ("base_colour", fields.CharField(null=True, max_length=50)),
                ("season", fields.CharField(null=True, max_length=20)),
                ("year", fields.SmallIntField(null=True)),
                ("usage", fields.CharField(null=True, max_length=50)),
                ("product_display_name", fields.TextField(null=True, unique=False)),
                ("price", fields.DecimalField(null=True, max_digits=12, decimal_places=2)),
                ("brand", fields.CharField(null=True, max_length=100)),
                ("text_for_ai", fields.TextField(null=True, unique=False)),
                ("search_vector", fields.TextField(generated=True, null=True, unique=False)),
            ],
            options={
                "table": "products",
                "app": "models",
                "indexes": [GinIndex(fields=["search_vector"], name="idx_products_search_vector")],
                "pk_attr": "id",
            },
            bases=["BaseModel"],
        ),
        ops.CreateModel(
            name="User",
            fields=[
                ("id", fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ("name", fields.CharField(max_length=100)),
                ("email", fields.CharField(unique=True, max_length=255)),
                ("password_hash", fields.CharField(max_length=255)),
                ("avatar_url", fields.CharField(null=True, max_length=500)),
                ("created_at", fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ("updated_at", fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={"table": "users", "app": "models", "pk_attr": "id"},
            bases=["BaseModel"],
        ),
    ]
