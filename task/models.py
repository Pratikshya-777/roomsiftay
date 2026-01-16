from django.contrib.auth.models import AbstractUser
from django.db import models
# from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    # username = models.CharField(
    #     max_length=150,
    #     unique=True,
    #     null=True,
    #     blank=True,
    #             )
    email = models.EmailField(unique=True) # Email must be unique
    is_owner = models.BooleanField(default=False)
    is_user = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email' # This tells Django: "Use email to log in"
    REQUIRED_FIELDS = ['username'] # Keep username here for AllAuth compatibility
    
    EMAIL_FIELD = 'email' 

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     image = models.ImageField(default='default.jpg', upload_to='profile_pics')

# Add this to task/models.py
class OwnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    auth_document = models.FileField(upload_to='documents/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.email}"

# class Owner(models.Model):
    
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
#     name = models.CharField(max_length=100) 
#     is_verified = models.BooleanField(default=False)
#     auth_proof = models.FileField(upload_to='owner_verifications/', null=True, blank=True)

#     def __str__(self):
#         return f"Owner: {self.name}"


class Listing(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    is_available = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BuyerReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified/Resolved'),

    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, default="Untitled")
    description = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __clstr__(self):
        return f"{self.title} by {self.user.username}"

# class PasswordResetOTP(models.Model):
#     user = models.ForeignKey('User', on_delete=models.CASCADE)
#     email_otp = models.CharField(max_length=6, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def is_expired(self):
#         return timezone.now() > self.created_at + timezone.timedelta(minutes=5)
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    def __str__(self):
        return self.user.email
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

class OwnerVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    document_file = models.FileField(upload_to='verification/') # Check this name!
    document_type = models.CharField(max_length=50, default='Citizenship')
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)