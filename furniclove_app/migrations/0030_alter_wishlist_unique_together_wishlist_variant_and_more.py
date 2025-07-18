# Generated by Django 5.1.4 on 2025-03-25 23:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0008_delete_wishlist'),
        ('furniclove_app', '0029_wishlist'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='wishlist',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='wishlist',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.colorvariant'),
        ),
        migrations.AlterUniqueTogether(
            name='wishlist',
            unique_together={('user', 'product', 'variant')},
        ),
    ]
