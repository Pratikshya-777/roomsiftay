
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
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
            # return redirect("role_redirect")

            if remember_me:
               
                request.session.set_expiry(1209600)
            else:
               
                request.session.set_expiry(0)

                return redirect("role_redirect")
            
#             role redirect rakhnu ko karad 
#             Old way (inside login_view)

# Role logic runs only during manual login

# Google login ❌ bypasses it

# Admin login ❌ bypasses it

# @login_required redirects ❌ bypass it

# ✅ role_redirect (current way)

# Role logic runs after ANY login

# Manual login ✅

# Google / GitHub login ✅

# Admin login ✅

# Session-based login ✅

            # if user.is_owner:
            #     return redirect("owner_dashboard")
            # else:
            #     return redirect("user_dashboard")

        # else:

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
        # We copy the POST data to modify it
        data = request.POST.copy()
        email = data.get("email")
        
        # FIX: Set username to be the same as email automatically
        if email:
            data['username'] = email 
        
        form = CustomUserCreationForm(data)

        if form.is_valid():
            user = form.save(commit=False)

            # Role Selection
            role = request.POST.get("role")
            if role == "owner":
                user.is_owner = True
                user.is_user = False
            else:
                user.is_user = True
                user.is_owner = False

            user.save()
            
            # Use the specific backend for manual login
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            messages.success(request, f"Welcome! Account created successfully.")
            return redirect("role_redirect") # Use your central redirect logic
            
    else:
        form = CustomUserCreationForm()

    return render(request, "task/register.html", {"form": form})

@login_required
def role_redirect(request):
    user = request.user

    if user.is_owner:
        return redirect("owner_dashboard")

    # default fallback
    return redirect("user_dashboard")

