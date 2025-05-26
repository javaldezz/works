from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserT
from django.db import transaction

## The purpose of this is to create a user_t instance when making
## a user in the terminal
@receiver(post_save, sender=User)
def create_usert_profile(sender, instance, created, **kwargs):
    if created:
        def create_usert():
            if not UserT.objects.filter(django_user=instance).exists():
                user_type = "Administrator" if instance.is_superuser else "Employee"
                UserT.objects.create(django_user=instance, user_type=user_type)
        
        transaction.on_commit(create_usert)