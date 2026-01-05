from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User  # Import your custom User model

admin.site.register(User, UserAdmin)