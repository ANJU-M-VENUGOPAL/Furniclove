# Generated by Django 5.1.4 on 2025-03-26 01:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0008_delete_wishlist'),
        ('furniclove_app', '0031_remove_cart_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.coupon'),
        ),
    ]
