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
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        role = request.COOKIES.get("social_role")
        # if role == "owner":
        #     user.is_owner = True
        #     user.is_user = False
        # else:
        user.is_user = True
        user.is_owner = True

        user.save()
        return user
