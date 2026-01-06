from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

@receiver(social_account_added)
def activate_social_user(request, sociallogin, **kwargs):
    user = sociallogin.user
    user.is_email_verified = True
    user.is_active = True
    user.save()
