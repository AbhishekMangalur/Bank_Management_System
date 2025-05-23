# Generated by Django 5.1.7 on 2025-03-31 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='loan',
            name='reason',
            field=models.CharField(max_length=255),
        ),
    ]
