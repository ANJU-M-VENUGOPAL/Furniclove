# Generated by Django 5.1.4 on 2025-03-14 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('furniclove_app', '0016_alter_cartitem_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
