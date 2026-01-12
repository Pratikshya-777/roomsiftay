from allauth.socialaccount.signals import social_account_added
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(social_account_added)
def activate_social_user(request, sociallogin, **kwargs):
    user = sociallogin.user
    user.is_email_verified = True
    user.is_active = True
    user.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    