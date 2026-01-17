from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        role = request.POST.get("role")

        if role == "owner":
            user.is_owner = True
            user.is_user = False
        else:
            user.is_user = True
            user.is_owner = False
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
 
    def is_open_for_signup(self, request, sociallogin):
        # ✅ THIS LINE REMOVES THE FINAL SIGNUP PAGE
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # 🔑 Social login has NO POST — use session instead
        role = request.session.get("social_role", "user")

        if role == "owner":
            user.is_owner = True
            user.is_user = False
        else:
            user.is_user = True
            user.is_owner = False

        user.save()
        return user
