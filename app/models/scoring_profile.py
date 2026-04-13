from enum import Enum

from tortoise import fields

from app.core.state_machine import StateMachine
from app.models.base_model import BaseModel


class ProfileStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


profile_state_machine = StateMachine(
    {
        ProfileStatus.DRAFT: [ProfileStatus.ACTIVE, ProfileStatus.ARCHIVED],
        ProfileStatus.ACTIVE: [ProfileStatus.ARCHIVED],
        ProfileStatus.ARCHIVED: [],
    }
)


class ScoringProfile(BaseModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    status = fields.CharEnumField(ProfileStatus, max_length=20, default=ProfileStatus.DRAFT)
    config = fields.JSONField()
    active_slot = fields.SmallIntField(null=True, unique=True)

    parent: fields.ForeignKeyNullableRelation["ScoringProfile"] = fields.ForeignKeyField(
        "models.ScoringProfile",
        null=True,
        related_name="children",
        on_delete=fields.SET_NULL,
    )

    activated_at = fields.DatetimeField(null=True)
    archived_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "scoring_profiles"
