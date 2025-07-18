# Generated by Django 5.2 on 2025-07-08 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('furniclove_app', '0042_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Failed', 'Failed'), ('Refunded', 'Refunded')], default='Pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'), ('Failed', 'Failed'), ('Returned', 'Returned')], default='Pending', max_length=20),
        ),
    ]
