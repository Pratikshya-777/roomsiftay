from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages




def home(request):
    return render(request, 'task/index.html')

def contact(request):
    return render(request, 'task/contact.html')

def about(request):
    return render(request, 'task/about.html')

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # get role from radio button
            role = request.POST.get("role", "user")

            # OPTIONAL: save role in profile if you have Profile model
            # user.profile.role = role
            # user.profile.save()

            messages.success(request, "Account created successfully!")
            return redirect("login")  # or home page

        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = UserCreationForm()

    return render(request, "task/register.html", {"form": form})
