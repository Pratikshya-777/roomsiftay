from django import forms
from django.contrib.auth.forms import UserCreationForm,PasswordResetForm
from django.contrib.auth import get_user_model
from .models import UserProfile, Listing,Message

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


class ListingStep1Form(forms.ModelForm):
    ROOM_TYPE_CHOICES = [
        ("private", "Private Room"),
        ("entire", "Entire Place"),
        ("shared", "Shared Room"),
    ]

    room_type = forms.ChoiceField(
        choices=ROOM_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True
        )
    class Meta:
        model = Listing
        fields = [
            "title",
            "room_type",
            "city",
            "area",
            "full_address",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Listing title"
            }),
            # "room_type": forms.TextInput(attrs={
            #     "class": "w-full px-4 py-3 rounded-xl border",
            #     "placeholder": "Room type (Single, Flat, Room)"
            # }),
            "city": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "City"
            }),
            "area": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Area / Locality"
            }),
            "full_address": forms.Textarea(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "rows": 3,
                "placeholder": "Full address (optional)"
            }),
        }


class ListingStep2Form(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "monthly_rent",
            "security_deposit",
            "bedrooms",
            "bathrooms",
            "floor_number",
            "is_furnished",
            "utilities_included",
            "wifi_available",
            "parking_available",

        ]

        widgets = {
            "monthly_rent": forms.NumberInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Monthly rent"
            }),
            "security_deposit": forms.NumberInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Security deposit (optional)"
            }),
            "bedrooms": forms.NumberInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Number of bedrooms"
            }),
            "bathrooms": forms.NumberInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Number of bathrooms"
            }),
            "floor_number": forms.NumberInput(attrs={
                "class": "w-full px-4 py-3 rounded-xl border",
                "placeholder": "Floor number (optional)"
            }),
            "is_furnished": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600"}),
            "utilities_included": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600"}),
            "wifi_available": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600"}),
            "parking_available": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600"}),
        }

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ListingStep3Form(forms.Form):
    photos = forms.ImageField(
        widget=MultipleFileInput(attrs={
            "id": "photos-input",
            "class": "hidden",
            "accept": "image/*",
            "class": "hidden"
        }),
        required=True
    )

    proof_photo = forms.ImageField(
        required=False
    )

    confirm_photos = forms.BooleanField(
        required=True
    )

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = [
            "owner",
            "status",
            "admin_note",
            "created_at",
            "updated_at",
        ]

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["text"]
        widgets = {
            "text": forms.TextInput(attrs={
                "class": "flex-1 rounded-xl border px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Type your message..."
            })
        }

