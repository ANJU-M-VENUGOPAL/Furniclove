# Generated by Django 5.1.4 on 2025-02-17 03:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('furniclove_app', '0011_cartitem_variant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='variant',
        ),
    ]
