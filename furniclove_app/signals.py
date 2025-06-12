from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Wallet


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)



@receiver(post_save, sender=UserProfile)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        print(f"Creating wallet for {instance.user.username}")
        Wallet.objects.create(user_profile=instance)
    else:
        if not hasattr(instance, 'wallet'):
            print(f"Creating wallet for existing user {instance.user.username}")
            Wallet.objects.create(user_profile=instance)
