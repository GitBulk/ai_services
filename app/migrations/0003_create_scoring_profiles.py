import functools
from json import dumps, loads

from tortoise import fields, migrations
from tortoise.fields.base import OnDelete
from tortoise.migrations import operations as ops

from app.models.scoring_profile import ProfileStatus


class Migration(migrations.Migration):
    dependencies = [("models", "0002_rename_avatar_url_to_avatar_path")]

    initial = False

    operations = [
        ops.CreateModel(
            name="ScoringProfile",
            fields=[
                ("id", fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ("name", fields.CharField(unique=True, max_length=255)),
                (
                    "status",
                    fields.CharEnumField(
                        default=ProfileStatus.DRAFT,
                        description="DRAFT: draft\nACTIVE: active\nARCHIVED: archived",
                        enum_type=ProfileStatus,
                        max_length=20,
                    ),
                ),
                ("config", fields.JSONField(encoder=functools.partial(dumps, separators=(",", ":")), decoder=loads)),
                ("active_slot", fields.SmallIntField(null=True)),
                (
                    "parent",
                    fields.ForeignKeyField(
                        "models.ScoringProfile",
                        source_field="parent_id",
                        null=True,
                        db_constraint=True,
                        to_field="id",
                        related_name="children",
                        on_delete=OnDelete.SET_NULL,
                    ),
                ),
                ("activated_at", fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ("archived_at", fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ("created_at", fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ("updated_at", fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={"table": "scoring_profiles", "app": "models", "pk_attr": "id"},
            bases=["BaseModel"],
        ),
    ]
