from .models import UserProfile

def navbar_profile(request):
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {"profile": profile}
    return {}
