
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Owner, Listing, BuyerReport



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
            
            # Set session expiry based on 'Remember Me'
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Browser close

            # IMPORTANT: This redirect MUST be inside the 'if user' block
            return redirect("role_redirect")

        else:
            # If authentication fails, show the error
            return render(request, "login.html", {
                "error": "Invalid email or password"
            })

    # If it's a GET request, just show the login page
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
            
            messages.success(request, f"Welcome! Account created successfully.")
            return redirect("login") 
            
    else:
        form = CustomUserCreationForm()

    return render(request, "task/register.html", {"form": form})

@login_required
def role_redirect(request):
    user = request.user
    selected_role = request.COOKIES.get('social_role')
    if user.is_user and user.is_owner:
        if selected_role == "owner":
            return redirect("owner_dashboard")
        else:
            # Default to user if cookie is missing or set to user
            return redirect("user_dashboard")

    # 3. For Manual Users (who only have ONE role set to True)
    if user.is_owner:
        return redirect("owner_dashboard")
    
    # Default fallback for everyone else
    return redirect("user_dashboard")
    return redirect("index")

def buyer(request):
    return render(request, 'task/buyer.html')

def saved_listings(request):
    # Logic to fetch user's saved items will go here later
    return render(request, 'task/saved_listings.html')

def submit_review(request):
    return render(request, 'task/review.html')

def report_issue(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        # Save the report to the database
        BuyerReport.objects.create(
            user=request.user,
            title=title,
            description=description
        )
        return redirect('buyer_dashboard')
    return render(request, 'task/report_issue.html')


def admin_view(request):
    owners = Owner.objects.all() # Or however you fetch owners
    listings = Listing.objects.all()
    
    # Fetch all reports from the database
    reports = BuyerReport.objects.all().order_by('-created_at')
    
    context = {
        'owners': owners,
        'listings': listings,
        'reports': reports, # This matches the {% for report in reports %} in your admin.html
    }
    return render(request, 'task/admin.html', context)
    # context = {
    #     'owners': Owner.objects.filter(is_verified=False),
    #     'listings': Listing.objects.all(),
    #     'reports': BuyerReport.objects.all().order_by('-created_at'),
    # }
    return render(request, 'task/admin.html', context)



