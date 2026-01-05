from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        This is for manual email registration.
        """
        user = super().save_user(request, user, form, commit=False)
        role = request.POST.get('role')
        if role == 'owner':
            user.is_owner = True
            user.is_user = False
        else:
            user.is_user = True
            user.is_owner = False
        
        user.save()
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        This is for Google/GitHub registration.
        """
        user = super().save_user(request, sociallogin, form)
        
        # If it's a brand new social account, give them a default role
        if not user.is_owner and not user.is_user:
            user.is_user = True  # Default Google users to 'User' role
            user.save()
        return user