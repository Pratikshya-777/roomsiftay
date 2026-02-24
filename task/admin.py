from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import User, BuyerReport
from .models import *

admin.site.register(OwnerProfile)
admin.site.register(Owner)
admin.site.register(Listing)
admin.site.register(ListingPhoto)
admin.site.register(Review)
# admin.site.register(UserProfile)
# admin.site.register(Notification)
# admin.site.register(Conversation)
# admin.site.register(Message)
admin.site.register(SavedListing)
admin.site.register(OwnerVerification)
# admin.site.register(PasswordResetOTP)

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User

    ordering = ('email',)
    list_display = ('email', 'is_staff', 'is_active')
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )


admin.site.register(BuyerReport)
