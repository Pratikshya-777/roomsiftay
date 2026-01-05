from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
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