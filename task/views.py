from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login




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

            role = request.POST.get("role", "user")
            # save role if you have a profile model

            login(request, user)  # ✅ AUTO LOGIN
            messages.success(request, "Welcome! Your account was created.")
            return redirect("/")  # home or dashboard

        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = UserCreationForm()

    return render(request, "task/register.html", {"form": form})

