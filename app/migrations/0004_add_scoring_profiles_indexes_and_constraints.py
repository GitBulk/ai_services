from tortoise import fields, migrations
from tortoise.migrations import operations as ops


class Migration(migrations.Migration):
    dependencies = [("models", "0003_create_scoring_profiles")]

    initial = False

    operations = [
        ops.AlterField(
            model_name="ScoringProfile",
            name="active_slot",
            field=fields.SmallIntField(null=True, unique=True),
        ),
        ops.RunSQL(
            sql="""
                ALTER TABLE scoring_profiles
                ADD CONSTRAINT ck_scoring_profiles_valid_slot
                CHECK (active_slot IS NULL OR active_slot IN (1, 2));
            """,
            reverse_sql="ALTER TABLE scoring_profiles DROP CONSTRAINT ck_scoring_profiles_valid_slot;",
        ),
        ops.RunSQL(
            sql="""
                ALTER TABLE scoring_profiles
                ADD CONSTRAINT ck_scoring_profiles_status_slot_consistency
                CHECK (
                    (status = 'active' AND active_slot IN (1, 2))
                    OR (status != 'active' AND active_slot IS NULL)
                );
            """,
            reverse_sql="ALTER TABLE scoring_profiles DROP CONSTRAINT ck_scoring_profiles_status_slot_consistency;",
        ),
    ]
