from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True) # Email must be unique
    is_owner = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)

    USERNAME_FIELD = 'email' # This tells Django: "Use email to log in"
    REQUIRED_FIELDS = ['username'] # Keep username here for AllAuth compatibility
