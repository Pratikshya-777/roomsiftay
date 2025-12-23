from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_owner = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)

    def __str__(self):
        return self.username


