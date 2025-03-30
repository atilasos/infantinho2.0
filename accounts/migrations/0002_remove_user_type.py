from django.db import migrations
from django.contrib.auth.models import Group

def create_default_groups(apps, schema_editor):
    Group.objects.get_or_create(name='teacher')
    Group.objects.get_or_create(name='student')
    Group.objects.get_or_create(name='guest')

def remove_default_groups(apps, schema_editor):
    Group.objects.filter(name__in=['teacher', 'student', 'guest']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='user_type',
        ),
        migrations.RunPython(create_default_groups, remove_default_groups),
    ] 