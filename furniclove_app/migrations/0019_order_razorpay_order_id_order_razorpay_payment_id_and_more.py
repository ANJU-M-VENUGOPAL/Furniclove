# Generated by Django 5.1.4 on 2025-03-15 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('furniclove_app', '0018_remove_order_razorpay_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'Cash on Delivery'), ('Razorpay', 'Razorpay')], default='COD', max_length=20),
        ),
    ]
