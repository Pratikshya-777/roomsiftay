from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    

class Owner(models.Model):
    name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

class OldListing(models.Model):
    title = models.CharField(max_length=200)
    # Status: use a red icon/dot in the template for 'Pending'
    status = models.CharField(max_length=20, default='Pending') 

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


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(default=5) # Optional: for star ratings
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username}"
    
class Listing(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Verification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings"
    )

    # STEP 1 — Basic Info
    title = models.CharField(max_length=200)
    room_type = models.CharField(max_length=50)
    city = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    full_address = models.TextField(blank=True)

    # STEP 2 — Pricing & Details
    monthly_rent = models.PositiveIntegerField(null=True, blank=True)
    security_deposit = models.PositiveIntegerField(blank=True, null=True)
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    floor_number = models.IntegerField(blank=True, null=True)

    # Facilities
    is_furnished = models.BooleanField(default=False)
    utilities_included = models.BooleanField(default=False)
    wifi_available = models.BooleanField(default=False)
    parking_available = models.BooleanField(default=False)

    # STEP 3 — Verification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    admin_note = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
class ListingPhoto(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="photos"
    )
    image = models.ImageField(upload_to="listing_photos/")
    is_proof = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.listing.id}" 


