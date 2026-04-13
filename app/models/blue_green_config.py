from tortoise import fields

from app.models.base_model import BaseModel


class BlueGreenConfig(BaseModel):
    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, unique=True)
    value = fields.CharField(max_length=255)
    last_computed_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "blue_green_configs"
