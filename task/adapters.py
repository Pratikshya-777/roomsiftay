from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):

    def login(self, request, user):
        messages.success(request, "Signup successful! You are now logged in.")
        return super().login(request, user) 
