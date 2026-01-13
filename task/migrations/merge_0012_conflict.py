from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('task', '0012_delete_profile'),
        ('task', '0012_review'),
    ]

    operations = [
        # No operations needed; this merge just tells Django both branches are applied
    ]
