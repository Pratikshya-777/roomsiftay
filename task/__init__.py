from django.dispatch import receiver
from allauth.account.signals import user_logged_in


@receiver(user_logged_in)
def assign_role_after_social_login(sender, request, user, **kwargs):
    """
    Assign role (owner/user) after Google or GitHub login
    using the role saved in cookie from register.html
    """

    # Only assign role if not already set
    if not user.is_owner and not user.is_user:
        role = request.COOKIES.get("social_role")

        if role == "owner":
            user.is_owner = True
            user.is_user = False
        else:
            # default to user if cookie missing or invalid
            user.is_user = True
            user.is_owner = False

        user.save()

        
