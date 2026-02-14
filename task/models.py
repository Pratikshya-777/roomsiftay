from django.contrib.auth.models import AbstractUser
from django.db import models
# from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True) # Email must be unique
    is_owner = models.BooleanField(default=False)
    is_user = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email' # This tells Django: "Use email to log in"
    REQUIRED_FIELDS = [] # Keep username here for AllAuth compatibility
    
    EMAIL_FIELD = 'email' 


class OldListing(models.Model):
    title = models.CharField(max_length=200)
    # Status: use a red icon/dot in the template for 'Pending'
    status = models.CharField(max_length=20, default='Pending') 


class OwnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    auth_document = models.FileField(upload_to='documents/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.email}"


class Owner(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    name = models.CharField(max_length=100) 
    is_verified = models.BooleanField(default=False)
    auth_proof = models.FileField(upload_to='owner_verifications/', null=True, blank=True)

    def __str__(self):
        return f"Owner: {self.name}"

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
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __clstr__(self):
        return f"{self.title} by {self.user.username}"


# class Notification(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
#     message = models.TextField()
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"Notification for {self.user.username}"

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
    ROOM_TYPE_CHOICES = [
        ("private", "Private Room"),
        ("entire", "Entire Place"),
        ("shared", "Shared Room"),
    ]

    room_type = models.CharField(
        max_length=50,
        choices=ROOM_TYPE_CHOICES
    )

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
    # room_type = models.CharField(max_length=50)
    city = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    full_address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

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
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_visible_to_public(self):
        return self.status == "approved" and self.is_active

    def can_owner_edit(self):
        return self.status in ["draft", "rejected"]

    def soft_delete(self):
        self.is_active = False
        self.save()

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


class OwnerVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    document_file = models.FileField(upload_to='verification/') # Check this name!
    document_type = models.CharField(max_length=50, default='Citizenship')
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

class Conversation(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buyer_conversations"
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owner_conversations"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("listing", "buyer", "owner")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Chat: {self.listing} | {self.buyer} → {self.owner}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    text = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender}"
    
class SavedListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")

    def __str__(self):
        return f"{self.user} saved {self.listing}"
