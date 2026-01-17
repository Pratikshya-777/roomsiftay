from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login,update_session_auth_hash, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from .forms import CustomUserCreationForm , UserProfileForm,ListingStep1Form,ListingStep2Form,ListingStep3Form
from django.conf import settings
from django.contrib import messages
from .models import Listing,ListingPhoto, BuyerReport, UserProfile, OwnerProfile, OwnerVerification,Owner
import random
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Review
from django.core.paginator import Paginator
from django.http import JsonResponse


# @login_required
def generate_otp():
    return str(random.randint(100000, 999999))

User = get_user_model()

def home(request):
    return render(request, 'task/index.html')


def contact(request):
    if request.method == "POST":
        name = request.POST.get("full_name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        full_message = f"""
        Name: {name}
        Email: {email}
        Role: {role}

        Message:
        {message}
        """

        send_mail(
            subject=f"[RoomSiftay Contact] {subject}",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        return render(request, "task/contact.html", {
            "success": True
        })

    return render(request, "task/contact.html")

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
            return render(request, "task/login.html", {
                "error": "Invalid email or password"
            })

    # If it's a GET request, just show the login page
    return render(request, "task/login.html")


@login_required
def owner_dashboard(request):
    # 1. Get or create the necessary profiles
    owner_profile, created = OwnerProfile.objects.get_or_create(user=request.user)
    
    verification, _ = OwnerVerification.objects.get_or_create(
        user=request.user,
        defaults={'document_type': 'Citizenship'}
    )

    # 2. Handle the Image Sync (If a file is uploaded from the dashboard)
    if request.method == "POST" and request.FILES.get('auth_document'):
        uploaded_file = request.FILES['auth_document']
        
        # Save to OwnerProfile (Dashboard view)
        owner_profile.auth_document = uploaded_file
        owner_profile.save()
        
        # Sync to OwnerVerification (Verification view)
        verification.document_file = uploaded_file
        verification.save()
        
        messages.success(request, "Identity document updated across your profile.")
        return redirect('owner_dashboard')

    # 3. Gather dashboard data
    listings = Listing.objects.filter(owner=request.user)
    total_count = listings.count()
    active_count = listings.filter(status='active').count()

    context = {
        'owner_profile': owner_profile,
        'verification': verification,
        'listings': listings,
        'total_count': total_count,
        'active_count': active_count,
    }
    return render(request, 'task/owner_dashboard.html', context)

def verification_page(request):
    # Fetch both records
    verification, _ = OwnerVerification.objects.get_or_create(user=request.user)
    owner_profile, _ = OwnerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if request.FILES.get('document_file'):
            uploaded_file = request.FILES['document_file']
            
            # 1. Update Verification Model
            verification.document_type = request.POST.get('document_type', 'Citizenship')
            verification.document_file = uploaded_file
            verification.is_verified = False
            verification.save()

            # 2. Update OwnerProfile Model (This fixes the Dashboard mismatch)
            owner_profile.auth_document = uploaded_file
            owner_profile.save()

            messages.success(request, "Document updated successfully! It is now under review.")
            return redirect('verification_page')
        else:
            messages.error(request, "Please select a file to upload.")

    return render(request, 'task/verification.html', {
        'verification': verification,
        'owner_profile': owner_profile # Pass this to ensure consistency in template
    })

def forgot_password(request):
    return render(request, "task/forgot_password.html")


def verify_otp(request):
    # user id stored in session during registration
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if entered_otp == user.email_otp:
            user.is_active = True
            user.is_email_verified = True
            user.email_otp = None
            user.save()

            # cleanup session
            del request.session["otp_user_id"]

            messages.success(request, "Email verified successfully. You can now login.")
            return redirect("login")

        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "task/verify_otp.html")

def resend_otp(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    user = User.objects.get(id=user_id)

    otp = generate_otp()
    user.email_otp = otp
    user.save()

    send_mail(
        subject="Your new RoomSiftay OTP",
        message=f"Your new OTP is {otp}",
        from_email="RoomSiftay <roomsiftay@gmail.com>",
        recipient_list=[user.email],
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify_otp")

# def user_dashboard(request):
#     return render(request, "task/user_dashboard.html")

def register(request):
    if request.method == "POST":
        data = request.POST.copy()
        email = data.get("email")

        # Auto-set username = email
        if email:
            data["username"] = email

        form = CustomUserCreationForm(data)

        if form.is_valid():
            user = form.save(commit=False)

            user.email = email
            user.username = email

            # Role selection
            role = request.POST.get("role" ,"buyer")
            if role == "owner":
                user.is_owner = True
                user.is_user = False
            else:
                user.is_user = True
                user.is_owner = False

            # 🔐 IMPORTANT: deactivate user until OTP verified
            user.is_active = False

            # Generate OTP
            otp = generate_otp()
            user.email_otp = otp

            user.save()

            # Send OTP email
            send_mail(
                subject="Verify your RoomSiftay account",
                message=f"Your OTP is {otp}",
                from_email="no-reply@roomsiftay.com",
                recipient_list=[user.email],
            )

            # Store user id in session for OTP verification
            request.session["otp_user_id"] = user.id

            messages.success(
                request,
                "We have sent a verification code to your email."
            )

            # 🔁 Redirect to OTP page (NOT login)
            return redirect("verify_otp")

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
            return redirect("buyer_dashboard")

    # 3. For Manual Users (who only have ONE role set to True)
    if user.is_owner:
        return redirect("owner_dashboard")
    
    # Default fallback for everyone else
    return redirect("buyer_dashboard")

@login_required
def buyer(request):
    return render(request, 'task/buyer_dashboard.html')

@login_required
def saved_listings(request):
    # Logic to fetch user's saved items will go here later
    return render(request, 'task/saved_listings.html')

# @login_required
# def submit_review(request):
#     return render(request, 'task/review.html')

@login_required
def report_issue(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        # 1. Validation to prevent the IntegrityError (NOT NULL)
        if not title:
            messages.error(request, "Please provide a title for your report.")
            return render(request, 'task/report_issue.html')

        # 2. Save the report to the database (Visible to Admin)
        BuyerReport.objects.create(
            user=request.user,
            title=title,
            description=description
        )
        
        # 3. Add success notification
        messages.success(request, "Your report has been submitted successfully!")
        
        # 4. Stay on the same page so they see the message
        return redirect('report_issue') 

    return render(request, 'task/report_issue.html')


@login_required
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
    # return render(request, 'task/admin.html', context)


def reset_password(request):
    if not request.session.get("otp_verified"):
        return redirect("forgot_password")
    completion = 0
    if request.user.get_full_name(): completion += 25
    if request.user.email: completion += 25
    if UserProfile.phone_number: completion += 25
    if UserProfile.profile_photo: completion += 25

    user = User.objects.get(id=request.session.get("reset_user_id"))
    profile_form = UserProfileForm(instance=UserProfile)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if password == confirm:
            user.set_password(password)
            user.email_otp = ""
            user.save()

            request.session.flush()
            messages.success(request, "Password reset successful.")
            return redirect("login")
        else:
            messages.error(request, "Passwords do not match")

    return render(request, "task/reset_password.html")


@login_required
def buyer_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Profile completion
    completion = 0
    if request.user.get_full_name(): completion += 25
    if request.user.email: completion += 25
    if profile.phone_number: completion += 25
    if profile.profile_photo: completion += 25

    profile_form = UserProfileForm(instance=profile)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":

        # DELETE profile photo
        if "delete_photo" in request.POST:
            if profile.profile_photo:
                profile.profile_photo.delete(save=False)
                profile.profile_photo = None
                profile.save()
            return redirect("buyer_profile")

        if "update_profile" in request.POST:
            profile_form = UserProfileForm(
                request.POST, request.FILES, instance=profile
            )
            if profile_form.is_valid():
                profile_form.save()
                return redirect("buyer_profile")

        # CHANGE password
        if "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                return redirect("buyer_profile")

    return render(request, "task/buyer_profile.html", {
        "profile": profile,
        "form": profile_form,
        "password_form": password_form,
        "completion": completion,
    })

def forgot_password(request):
    return render(request, "task/forgot_password.html")



def reset_password(request):
    return render(request, "task/reset_password.html")


@login_required
@require_POST
def resolve_report(request, report_id):
    try:
        report = BuyerReport.objects.get(id=report_id)
        report.status = 'verified'  # Ensure you have a status field in your model
        report.save()
        return JsonResponse({'status': 'success'})
    except BuyerReport.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
def logout(request):
    auth_logout(request)
    return redirect("login")

@login_required
def owner_add_listingstep1(request):
        if request.method == "POST":
            form = ListingStep1Form(request.POST)
            if form.is_valid():
                listing = form.save(commit=False)

            # attach owner
            listing.owner = request.user  # adjust if you use a profile
            listing.status = "draft"

            listing.save()

            # store listing id in session
            request.session["listing_id"] = listing.id

            return redirect("owner_add_listingstep2")
        else:
            form = ListingStep1Form()
        return render(request, "task/owner_add_listing/owner_add_listingstep1.html" , {"form": form})

def owner_add_listingstep2(request):
    listing_id = request.session.get("listing_id")

    if not listing_id:
        return redirect("owner_add_listingstep1")

    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)

    if request.method == "POST":
        form = ListingStep2Form(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            return redirect("owner_add_listingstep3")
    else:
        form = ListingStep2Form(instance=listing)
    return render(request, "task/owner_add_listing/owner_add_listingstep2.html",{"form": form})


def owner_add_listingstep3(request):
    listing_id = request.session.get("listing_id")
    if not listing_id:
        return redirect("owner_add_listingstep1")

    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user
    )

    if request.method == "POST":
        photos = request.FILES.getlist("photos")
        proof = request.FILES.get("proof_photo")
        confirm = request.POST.get("confirm_photos")

        # 🔍 Debug (remove later)
        print("FILES:", request.FILES)

        if len(photos) < 3:
            messages.error(request, "Upload at least 3 room photos.")
            return redirect("owner_add_listingstep3")

        if not confirm:
            messages.error(request, "Please confirm the photos.")
            return redirect("owner_add_listingstep3")

        # Save room photos
        for image in photos:
            ListingPhoto.objects.create(
                listing=listing,
                image=image,
                is_proof=False
            )

        # Save proof photo (optional)
        if proof:
            ListingPhoto.objects.create(
                listing=listing,
                image=proof,
                is_proof=True
            )

        return redirect("owner_add_listingstep4")

    return render(
        request,
        "task/owner_add_listing/owner_add_listingstep3.html"
    )


def owner_add_listingstep4(request):
    listing_id = request.session.get("listing_id")
    if not listing_id:
        return redirect("owner_add_listingstep1")

    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user
    )

    photos = listing.photos.filter(is_proof=False)
    proof_photo = listing.photos.filter(is_proof=True).first()

    if request.method == "POST":
        action = request.POST.get("action")

        # SAVE AS DRAFT
        if action == "draft":
            listing.status = "draft"
            listing.save()

            messages.success(request, "Listing saved as draft.")
            return redirect("owner_dashboard")

        # SUBMIT FOR VERIFICATION
        if action == "submit":
            listing.status = "pending"
            listing.save()

            # Clear session
            request.session.pop("listing_id", None)

            messages.success(
                request,
                "Listing submitted for verification."
            )
            return redirect("owner_dashboard")

    return render(
        request,
        "task/owner_add_listing/owner_add_listingstep4.html",
        {
            "listing": listing,
            "photos": photos,
            "proof_photo": proof_photo,
        }
    )

def provide_review(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        rating = request.POST.get('rating')
        if comment:
            Review.objects.create(user=request.user, comment=comment, rating=int(rating))
            messages.success(request, "Thank you for your review!")
            return JsonResponse({'status': 'success', 'message': 'Your review is submitted!'})
            # return redirect('buyer_dashboard') # Redirects to landing page
    return render(request, 'task/provide_review.html')

def home(request):
    # Fetch all reviews to show on the landing page
    recent_reviews = Review.objects.all().order_by('-created_at')[:5]
    return render(request, 'task/index.html', {'reviews': recent_reviews})

def all_reviews(request):
    # Fetch every review in the database
    full_reviews = Review.objects.all().order_by('-created_at')
    paginator = Paginator(full_reviews, 5) 
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'task/all_reviews.html', {'page_obj': page_obj})

@login_required
def owner_listing(request):
    drafts = Listing.objects.filter(
        owner=request.user,
        status="draft"
    )

    pending = Listing.objects.filter(
        owner=request.user,
        status="pending"
    )

    approved = Listing.objects.filter(
        owner=request.user,
        status="approved"
    )

    return render(
        request,
        "task/owner_listing.html",
        {
            "drafts": drafts,
            "pending": pending,
            "approved": approved,
        }
    )

@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user,
    )

    # put listing back into session
    request.session["listing_id"] = listing.id

    # redirect to step 1 (or step 2 / 3 if you want)
    return redirect("owner_add_listingstep1")