from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm , UserProfileForm
from django.conf import settings
from django.contrib import messages
from .models import Owner, Listing, BuyerReport, UserProfile
import random
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm

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
            return render(request, "login.html", {
                "error": "Invalid email or password"
            })

    # If it's a GET request, just show the login page
    return render(request, "task/login.html")



def owner_dashboard(request):
    return render(request, "task/owner_dashboard.html")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            user.email_otp = otp
            user.save()

            send_mail(
                subject="RoomSiftay Password Reset OTP",
                message=f"Your OTP is {otp}",
                from_email="no-reply@roomsiftay.com",
                recipient_list=[email],
                fail_silently=False,
            )

            request.session["reset_user_id"] = user.id
            messages.success(request, "OTP sent to your email.")
            return redirect("verify_otp")

        except User.DoesNotExist:
            messages.error(request, "Email not registered.")

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
            role = request.POST.get("role")
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
        return redirect('buyer.html')
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
