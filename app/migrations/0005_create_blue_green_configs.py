from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0004_add_scoring_profiles_indexes_and_constraints')]

    initial = False

    operations = [
        ops.CreateModel(
            name='BlueGreenConfig',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('key', fields.CharField(unique=True, max_length=255)),
                ('value', fields.CharField(max_length=255)),
                ('last_computed_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'blue_green_configs', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel'],
        ),
    ]
