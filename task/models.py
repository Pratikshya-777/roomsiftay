from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'
    

class Owner(models.Model):
    name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

class Listing(models.Model):
    title = models.CharField(max_length=200)
    # Status: use a red icon/dot in the template for 'Pending'
    status = models.CharField(max_length=20, default='Pending') 

class BuyerReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, default="Untitled")
    description = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __clstr__(self):
        return f"{self.title} by {self.user.username}"