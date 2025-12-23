
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
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


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)

            if remember_me:
               
                request.session.set_expiry(1209600)
            else:
               
                request.session.set_expiry(0)

            if user.is_owner:
                return redirect("owner_dashboard")
            else:
                return redirect("user_dashboard")

        else:
            return render(request, "login.html", {
                "error": "Invalid email or password"
            })

    return render(request, "login.html")


def owner_dashboard(request):
    return render(request, "task/owner_dashboard.html")


def user_dashboard(request):
    return render(request, "task/user_dashboard.html")
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
