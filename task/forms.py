from django import forms
from django.contrib.auth.forms import UserCreationForm,PasswordResetForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # FIX 1: Add a comma after "email" to make it a tuple. 
        # FIX 2: Include "username" here so the form doesn't crash, 
        # but we will hide it in the __init__ below.
        fields = ("email", "username")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # FIX 3: Hide the username field from the UI entirely
        if 'username' in self.fields:
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['username'].required = False

        # Your Tailwind styling loop
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 transition shadow-sm outline-none',
                'placeholder': f'Enter {field_name.replace("_", " ").capitalize()}'
            })

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone_number", "profile_photo"]

        widgets = {
            "phone_number": forms.TextInput(attrs={
                "class": "w-full p-2 border rounded-lg",
                "placeholder": "Phone number"
            }),
        }

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-3 rounded-xl border border-gray-300 bg-white focus:ring-indigo-500 focus:border-indigo-500 outline-none",
            "placeholder": "Enter your email address"
        })
    )