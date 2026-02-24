from datetime import timedelta
from math import radians, cos, sin, asin, sqrt  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, update_session_auth_hash, get_user_model, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ListingForm, UserProfileForm, ListingStep1Form, ListingStep2Form, ListingStep3Form, MessageForm
from django.conf import settings
from django.contrib import messages
from .models import Listing, ListingPhoto, BuyerReport, Notification, UserProfile, OwnerProfile, OwnerVerification, Owner, Conversation, Message, SavedListing, Review
import random
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import math

User = get_user_model()


# ADD THIS FUNCTION HERE (at the top, after imports)
def haversine(lon1, lat1, lon2, lat2):
    """Calculate the distance between two points on earth in km"""
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return round(km, 2)


def generate_otp():
    return str(random.randint(100000, 999999))


def home(request):
    # Fetch all reviews to show on the landing page
    recent_reviews = Review.objects.all().order_by('-created_at')[:5]
    return render(request, 'task/index.html', {'reviews': recent_reviews})


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

            return redirect("role_redirect")

        else:
            return render(request, "task/login.html", {
                "error": "Invalid email or password"
            })

    return render(request, "task/login.html")


@login_required
def owner_dashboard(request):
    request.session["mode"] = "owner"
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
    all_listings = Listing.objects.filter(owner=request.user, is_active=True)
    total_count = all_listings.count()
    active_count = all_listings.filter(status='approved', is_available=True).count()
    
    # Limit to 6 for dashboard display
    listings = all_listings.order_by('-created_at')[:6]
    show_view_all = total_count > 6

    context = {
        'owner_profile': owner_profile,
        'verification': verification,
        'listings': listings,
        'total_count': total_count,
        'active_count': active_count,
        'show_view_all': show_view_all,
    }
    return render(request, 'task/owner_dashboard.html', context)


def verification_page(request):
    request.session["mode"] = "owner"
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
        'owner_profile': owner_profile
    })


def forgot_password(request):
    return render(request, "task/forgot_password.html")


def verify_otp(request):
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

            del request.session["otp_user_id"]

            messages.success(request, "Email verified successfully. You can now login.")
            return redirect("buyer")

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


def register(request):
    if request.method == "POST":
        data = request.POST.copy()
        email = data.get("email")

        if email:
            data["username"] = email

        form = CustomUserCreationForm(data)

        if form.is_valid():
            user = form.save(commit=False)

            user.email = email
            user.username = email

            role = request.POST.get("role", "buyer")
            if role == "owner":
                user.is_owner = True
                user.is_user = False
            else:
                user.is_user = True
                user.is_owner = False

            user.is_active = False

            otp = generate_otp()
            user.email_otp = otp

            user.save()

            send_mail(
                subject="Verify your RoomSiftay account",
                message=f"Your OTP is {otp}",
                from_email="no-reply@roomsiftay.com",
                recipient_list=[user.email],
            )

            request.session["otp_user_id"] = user.id

            messages.success(
                request,
                "We have sent a verification code to your email."
            )

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
            return redirect("buyer_dashboard")

    if user.is_owner:
        return redirect("owner_dashboard")
    
    return redirect("buyer_dashboard")


@login_required
def buyer_dashboard(request):
    request.session["mode"] = "buyer"

    user = request.user

    # Only count saved listings that are still active, approved, AND available
    saved_count = SavedListing.objects.filter(
        user=user,
        listing__is_active=True,
        listing__status='approved',
        listing__is_available=True  # Only count available ones
    ).count()

    conversations = Conversation.objects.filter(buyer=user)
    unread_messages = Message.objects.filter(
        conversation__in=conversations,
        is_read=False
    ).exclude(sender=user).count()

    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

    one_week_ago = timezone.now() - timedelta(days=7)
    new_listings_count = Listing.objects.filter(
        status="approved",
        is_active=True,
        created_at__gte=one_week_ago
    ).count()

    # Filter to only show active, approved, AND AVAILABLE listings in recently saved
    recent_saved = SavedListing.objects.filter(
        user=user,
        listing__is_active=True,
        listing__status='approved',
        listing__is_available=True  # ADD THIS - hide unavailable from dashboard
    ).select_related("listing").order_by("-saved_at")[:3]

    recent_conversations = conversations[:3]

    context = {
        "saved_count": saved_count,
        "unread_messages": unread_messages,
        "unread_notifications": unread_notifications,
        "new_listings_count": new_listings_count,
        "recent_saved": recent_saved,
        "recent_conversations": recent_conversations,
    }

    return render(request, "task/buyer_dashboard.html", context)


@login_required
def nearby_listings(request):
    """API endpoint to get nearby listings based on user's location"""
    try:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        radius = request.GET.get('radius', 5)  # Default 5km
        
        if not lat or not lng:
            return JsonResponse({'error': 'Location required', 'listings': []})
        
        lat = float(lat)
        lng = float(lng)
        radius = float(radius)
        
        # Get all approved, available listings with coordinates
        all_listings = Listing.objects.filter(
            status='approved',
            is_available=True,
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        nearby = []
        for listing in all_listings:
            try:
                distance = haversine(lng, lat, float(listing.longitude), float(listing.latitude))
                if distance <= radius:
                    # Get first photo
                    first_photo = listing.photos.first()
                    image_url = first_photo.image.url if first_photo else None
                    
                    nearby.append({
                        'id': listing.id,
                        'title': listing.title,
                        'city': listing.city or '',
                        'area': listing.area or '',
                        'rent': str(listing.monthly_rent),
                        'image': image_url,
                        'distance': distance,
                        'latitude': str(listing.latitude),
                        'longitude': str(listing.longitude),
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        
        return JsonResponse({'listings': nearby})
    
    except Exception as e:
        return JsonResponse({'error': str(e), 'listings': []})


@login_required
def report_issue(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not title:
            messages.error(request, "Please provide a title for your report.")
            return render(request, 'task/report_issue.html')

        BuyerReport.objects.create(
            user=request.user,
            title=title,
            description=description
        )
        
        messages.success(request, "Your report has been submitted successfully!")
        return redirect('report_issue')

    return render(request, 'task/report_issue.html')


@staff_member_required
def admin_view(request):

    pending_verifications = OwnerVerification.objects.filter(
        is_verified=False,              # Not yet approved
        document_file__isnull=False     # Has uploaded a file
    ).exclude(
        document_file=''                # Exclude empty strings
    ).select_related("user")

    listings = Listing.objects.filter(status__in=["pending"])
    reports = BuyerReport.objects.all().order_by('-id')
    
    context = {
        'pending_verifications': pending_verifications,
        'listings': listings,
        'pending_reports': reports.filter(status='pending'),
        'verified_reports': reports.filter(status='verified'),
    }
    return render(request, 'task/admin/admin.html', context)


@staff_member_required
def admin_listing_detail(request, listing_id):
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        status__in=["pending", "approved", "rejected"]
    )

    if request.method == "POST":
        action = request.POST.get("action")
        admin_note = request.POST.get("admin_note", "").strip()

        if action == "approve":
            listing.status = "approved"
            listing.is_active = True
            listing.admin_note = ""
            listing.save()

        elif action == "reject":
            if not admin_note:
                return render(request, "task/admin/admin_listing_detail.html", {
                    "listing": listing,
                    "error": "Rejection reason is required."
                })
            listing.status = "rejected"
            listing.is_active = False
            listing.admin_note = admin_note
            listing.save()

        return redirect("admin_dashboard")

    return render(request, "task/admin/admin_listing_detail.html", {
        "listing": listing
    })


@staff_member_required
def admin_listings(request):
    listings = Listing.objects.filter(
        status__in=["pending"]
    ).order_by("-created_at")

    return render(request, "task/admin/admin_listings.html", {
        "listings": listings
    })


def reset_password(request):
    if not request.session.get("otp_verified"):
        return redirect("forgot_password")
    
    user = User.objects.get(id=request.session.get("reset_user_id"))

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
    
    completion = 0
    if request.user.get_full_name(): completion += 25
    if request.user.email: completion += 25
    if profile.phone_number: completion += 25
    if profile.profile_photo: completion += 25

    profile_form = UserProfileForm(instance=profile)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":

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
                request.user.first_name = request.POST.get("first_name")
                request.user.last_name = request.POST.get("last_name")
                request.user.save()

                return redirect("buyer_profile")

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


@login_required
@require_POST
def resolve_report(request, report_id):
    try:
        report = BuyerReport.objects.get(id=report_id)
        report.status = 'verified'
        report.save()
        return JsonResponse({'status': 'success'})
    except BuyerReport.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


def logout(request):
    auth_logout(request)
    return redirect("login")


@login_required
def owner_add_listingstep1(request):
    request.session["mode"] = "owner"
    
    # Check verification status
    owner_profile, _ = OwnerProfile.objects.get_or_create(user=request.user)
    is_verified = owner_profile.is_verified
    
    # If not verified, show the page but don't process form
    if not is_verified:
        form = ListingStep1Form()
        return render(request, "task/owner_add_listing/owner_add_listingstep1.html", {
            "form": form,
            "is_verified": False,
            "owner_profile": owner_profile,
        })
    
    # Verified users can proceed
    if request.method == "POST":
        form = ListingStep1Form(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.status = "draft"
            listing.save()
            request.session["listing_id"] = listing.id
            return redirect("owner_add_listingstep2")
    else:
        form = ListingStep1Form()

    return render(request, "task/owner_add_listing/owner_add_listingstep1.html", {
        "form": form,
        "is_verified": True,
        "owner_profile": owner_profile,
    })


def owner_add_listingstep2(request):
    request.session["mode"] = "owner"
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
    return render(request, "task/owner_add_listing/owner_add_listingstep2.html", {"form": form})


@login_required
def owner_add_listingstep3(request):
    request.session["mode"] = "owner"
    listing_id = request.session.get("listing_id")
    if not listing_id:
        return redirect("owner_add_listingstep1")

    listing = get_object_or_400(
        Listing,
        id=listing_id,
        owner=request.user
    )

    if request.method == "POST":
        photos = request.FILES.getlist("photos")
        proof = request.FILES.get("proof_photo")
        confirm = request.POST.get("confirm_photos")

        existing_count = listing.photos.filter(is_proof=False).count()
        total_count = existing_count + len(photos)

        if total_count < 3:
            messages.error(request, "Upload at least 3 room photos.")
            return redirect("owner_add_listingstep3")

        if not confirm:
            messages.error(request, "Please confirm the photos.")
            return redirect("owner_add_listingstep3")

        for image in photos:
            ListingPhoto.objects.create(
                listing=listing,
                image=image,
                is_proof=False
            )

        if proof:
            listing.photos.filter(is_proof=True).delete()

            ListingPhoto.objects.create(
                listing=listing,
                image=proof,
                is_proof=True
            )

        return redirect("owner_add_listingstep4")

    proof_photo = listing.photos.filter(is_proof=True).first()

    return render(
        request,
        "task/owner_add_listing/owner_add_listingstep3.html",
        {
            "listing": listing,
            "proof_photo": proof_photo,
        }
    )


def owner_add_listingstep4(request):
    request.session["mode"] = "owner"
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

        if action == "draft":
            listing.status = "draft"
            listing.save()

            messages.success(request, "Listing saved as draft.")
            return redirect("owner_dashboard")

        if action == "submit":
            listing.status = "pending"
            listing.save()

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
    return render(request, 'task/provide_review.html')


def all_reviews(request):
    full_reviews = Review.objects.all().order_by('-created_at')
    paginator = Paginator(full_reviews, 5)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'task/all_reviews.html', {'page_obj': page_obj})


@login_required
def owner_listing(request):
    request.session["mode"] = "owner"
    
    availability_filter = request.GET.get('filter', 'all')
    
    drafts = Listing.objects.filter(
        owner=request.user,
        status="draft",
        is_active=True
    )

    pending = Listing.objects.filter(
        owner=request.user,
        status="pending",
        is_active=True
    )

    approved_base = Listing.objects.filter(
        owner=request.user,
        status="approved",
        is_active=True
    )
    
    if availability_filter == 'available':
        approved = approved_base.filter(is_available=True)
    elif availability_filter == 'unavailable':
        approved = approved_base.filter(is_available=False)
    else:
        approved = approved_base
    
    approved_all_count = approved_base.count()
    approved_available_count = approved_base.filter(is_available=True).count()
    approved_unavailable_count = approved_base.filter(is_available=False).count()
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    trash_count = Listing.objects.filter(
        owner=request.user,
        is_active=False,
        deleted_at__isnull=False,
        deleted_at__gte=seven_days_ago
    ).count()

    return render(
        request,
        "task/owner_listing/owner_listing.html",
        {
            "drafts": drafts,
            "pending": pending,
            "approved": approved,
            "availability_filter": availability_filter,
            "approved_all_count": approved_all_count,
            "approved_available_count": approved_available_count,
            "approved_unavailable_count": approved_unavailable_count,
            "trash_count": trash_count,
        }
    )


@login_required
def owner_listing_details(request, pk):
    request.session["mode"] = "owner"
    listing = get_object_or_404(
        Listing,
        pk=pk,
        owner=request.user
    )

    return render(
        request,
        "task/owner_listing/owner_listing_details.html",
        {"listing": listing}
    )


@login_required
def submit_listing(request, pk):
    request.session["mode"] = "owner"
    listing = get_object_or_404(
        Listing,
        pk=pk,
        owner=request.user,
        status="draft"
    )

    listing.status = "pending"
    listing.save()

    return redirect("owner_listing_details", pk=pk)


@login_required
def owner_edit_listing(request, pk):
    request.session["mode"] = "owner"
    listing = get_object_or_404(
        Listing,
        pk=pk,
        owner=request.user
    )

    if listing.status == "approved":
        messages.warning(
            request,
            "Approved listings cannot be edited. Please contact admin."
        )
        return redirect("owner_listing_detail", pk=pk)

    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)

        if form.is_valid():
            form.save()

            if "image" in request.FILES:
                ListingPhoto.objects.create(
                    listing=listing,
                    image=request.FILES["image"]
                )

            messages.success(request, "Listing updated successfully.")
            return redirect("owner_listing_detail", pk=pk)

    else:
        form = ListingForm(instance=listing)

    return render(
        request,
        "task/owner_listing/owner_edit_listing.html",
        {
            "form": form,
            "listing": listing,
        }
    )


@login_required
def start_chat(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.user == listing.owner:
        return redirect("chat_list")

    conversation, created = Conversation.objects.get_or_create(
        listing=listing,
        buyer=request.user,
        owner=listing.owner,
    )

    return redirect("chat_room", conversation_id=conversation.id)


@login_required
def chat_list(request):
    conversations = Conversation.objects.filter(
        buyer=request.user
    ) | Conversation.objects.filter(
        owner=request.user
    )

    conversations = conversations.order_by("-created_at")

    return render(request, "task/chat/chat_list.html", {
        "conversations": conversations
    })


@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.buyer, conversation.owner]:
        return redirect("chat_list")

    # Mark messages as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    chat_messages = conversation.messages.order_by("created_at")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()
            return redirect("chat_room", conversation_id=conversation.id)
    else:
        form = MessageForm()

    return render(request, "task/chat/chat_room.html", {
        "conversation": conversation,
        "messages": chat_messages,
        "form": form,
    })


def buyer_search_room(request):
    request.session["mode"] = "buyer"
    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    room_type = request.GET.get("room_type", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "").strip()
    lat = request.GET.get("lat", "").strip()
    lng = request.GET.get("lng", "").strip()
    radius_km = request.GET.get("radius_km", "").strip()

    listings = Listing.objects.filter(
        status="approved",
        is_active=True
    ).prefetch_related("photos")

    if query:
        listings = listings.filter(
            Q(city__icontains=query) | Q(area__icontains=query)
        )

    if location:
        listings = listings.filter(
            Q(city__icontains=location) | Q(area__icontains=location)
        )

    if room_type:
        listings = listings.filter(room_type=room_type)

    if request.GET.get("wifi"):
        listings = listings.filter(wifi_available=True)

    if request.GET.get("parking"):
        listings = listings.filter(parking_available=True)

    if request.GET.get("furnished"):
        listings = listings.filter(is_furnished=True)

    if request.GET.get("utilities"):
        listings = listings.filter(utilities_included=True)

    if request.GET.get("ac"):
        listings = listings.filter(ac_available=True)

    if request.GET.get("water"):
        listings = listings.filter(water_24hrs=True)

    if request.GET.get("lift"):
        listings = listings.filter(lift_available=True)

    if request.GET.get("pet"):
        listings = listings.filter(pet_allowed=True)

    if request.GET.get("balcony"):
        listings = listings.filter(has_balcony=True)

    if min_price:
        try:
            listings = listings.filter(monthly_rent__gte=int(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            listings = listings.filter(monthly_rent__lte=int(max_price))
        except ValueError:
            pass

    def haversine(lon1, lat1, lon2, lat2):
        """Calculate the distance between two points on earth in km"""
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return round(km, 2)

    if lat and lng and radius_km:
        try:
            lat_f = float(lat)
            lng_f = float(lng)
            radius_f = float(radius_km)

            lat_delta = radius_f / 111.0
            lng_delta = radius_f / (111.0 * math.cos(math.radians(lat_f)) or 1)

            listings = listings.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                latitude__gte=lat_f - lat_delta,
                latitude__lte=lat_f + lat_delta,
                longitude__gte=lng_f - lng_delta,
                longitude__lte=lng_f + lng_delta,
            )

            filtered = []
            for l in listings:
                if l.latitude is None or l.longitude is None:
                    continue
                dist = haversine(lng_f, lat_f, float(l.longitude), float(l.latitude))
                if dist <= radius_f:
                    filtered.append(l)
            listings = filtered

        except ValueError:
            pass

    if sort == "newest":
        listings = listings.order_by("-created_at")
    elif sort == "price_low":
        listings = listings.order_by("monthly_rent")
    elif sort == "price_high":
        listings = listings.order_by("-monthly_rent")

    context = {
        "listings": listings,
        "q": query,
        "location": location,
        "room_type": room_type,
        "min_price": min_price,
        "max_price": max_price,
        "lat": lat,
        "lng": lng,
        "radius_km": radius_km,
        "sort": sort,
    }

    return render(request, "task/buyer_search_room/buyer_search_room.html", context)


def buyer_listing_detail(request, listing_id):
    request.session["mode"] = "buyer"
    listing = get_object_or_404(
        Listing.objects.prefetch_related("photos"),
        id=listing_id,
        status="approved",
        is_active=True
    )

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedListing.objects.filter(
            user=request.user, listing=listing
        ).exists()

    return render(request, "task/buyer_search_room/buyer_listing_detail.html", {
        "listing": listing,
        "is_saved": is_saved
    })


@login_required
def save_listing(request, listing_id):
    request.session["mode"] = "buyer"
    listing = get_object_or_404(Listing, id=listing_id)

    saved_obj, created = SavedListing.objects.get_or_create(
        user=request.user,
        listing=listing
    )

    if not created:
        saved_obj.delete()
        messages.info(request, "Removed from saved listings.")
    else:
        messages.success(request, "Listing saved successfully ❤️")

    return redirect("buyer_listing_detail", listing_id=listing_id)


@login_required
def saved_listings(request):
    # Only show saved listings where listing is still active (not deleted)
    saved = (
        SavedListing.objects
        .filter(
            user=request.user,
            listing__is_active=True,        # Not deleted
            listing__status='approved'       # Approved by admin
        )
        .select_related("listing", "listing__owner")
        .prefetch_related("listing__photos")
    )

    return render(
        request,
        "task/buyer_search_room/saved_listings.html",
        {"saved_listings": saved},
    )


# ================= LISTING ACTIONS =================

@login_required
@require_POST
def toggle_availability(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    
    # Toggle availability
    listing.is_available = not listing.is_available
    listing.save()
    
    # If listing became UNAVAILABLE, notify users who saved it
    if not listing.is_available:
        saved_by_users = SavedListing.objects.filter(listing=listing).select_related('user')
        
        for saved in saved_by_users:
            Notification.objects.create(
                user=saved.user,
                title="Saved Listing Unavailable",
                message=f"'{listing.title}' in {listing.city} is no longer available.",
                notification_type="listing_unavailable",
                listing=listing
            )
    
    # If listing became AVAILABLE again, notify users who saved it
    else:
        saved_by_users = SavedListing.objects.filter(listing=listing).select_related('user')
        
        for saved in saved_by_users:
            Notification.objects.create(
                user=saved.user,
                title="Saved Listing Available Again!",
                message=f"Good news! '{listing.title}' in {listing.city} is available again.",
                notification_type="listing_available",
                listing=listing
            )
    
    if listing.is_available:
        messages.success(request, "Listing marked as available.")
    else:
        messages.warning(request, "Listing marked as unavailable.")
    
    return redirect('owner_listing_details', pk=listing_id)


@login_required
def delete_listing(request, listing_id):
    """Soft delete - moves listing to trash"""
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user
    )

    if request.method == "POST":
        listing.is_active = False
        listing.deleted_at = timezone.now()
        listing.save()
        messages.success(request, f"'{listing.title}' moved to trash. You can restore it within 7 days.")

    return redirect("owner_listing")


@login_required
def deleted_listing(request):
    """Show all soft-deleted listings (trash)"""
    request.session["mode"] = "owner"
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    trash_listings = Listing.objects.filter(
        owner=request.user,
        is_active=False,
        deleted_at__isnull=False,
        deleted_at__gte=seven_days_ago
    ).order_by('-deleted_at')
    
    # Auto-cleanup: Delete listings older than 7 days
    old_listings = Listing.objects.filter(
        owner=request.user,
        is_active=False,
        deleted_at__isnull=False,
        deleted_at__lt=seven_days_ago
    )
    old_count = old_listings.count()
    old_listings.delete()
    
    if old_count > 0:
        messages.info(request, f"{old_count} listing(s) were permanently deleted (older than 7 days).")
    
    context = {
        'trash_listings': trash_listings,
        'trash_count': trash_listings.count(),
    }
    
    return render(request, 'task/owner_listing/deleted_listing.html', context)


@login_required
def restore_listing(request, listing_id):
    """Restore a listing from trash"""
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user,
        is_active=False
    )
    
    if request.method == "POST":
        listing.is_active = True
        listing.deleted_at = None
        listing.save()
        messages.success(request, f"'{listing.title}' has been restored successfully.")
    
    return redirect("deleted_listing")


@login_required
def permanent_delete_listing(request, listing_id):
    """Permanently delete a listing (no recovery)"""
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        owner=request.user,
        is_active=False
    )
    
    if request.method == "POST":
        title = listing.title
        listing.delete()
        messages.success(request, f"'{title}' has been permanently deleted.")
    
    return redirect("deleted_listing")


@login_required
def empty_trash(request):
    """Permanently delete all listings in trash"""
    if request.method == "POST":
        deleted_count = Listing.objects.filter(
            owner=request.user,
            is_active=False,
            deleted_at__isnull=False
        ).delete()[0]
        
        messages.success(request, f"{deleted_count} listing(s) permanently deleted.")
    
    return redirect("deleted_listing")


# ================= ADMIN VERIFICATION =================

@staff_member_required
def admin_verification(request):
    """List all pending verifications"""
    pending_verifications = OwnerVerification.objects.filter(
        is_verified=False,
        document_file__isnull=False
    ).exclude(document_file='').select_related('user')
    
    verified_verifications = OwnerVerification.objects.filter(
        is_verified=True
    ).select_related('user').order_by('-id')[:10]
    
    context = {
        'pending_verifications': pending_verifications,
        'verified_verifications': verified_verifications,
    }
    
    return render(request, 'task/admin/admin_verification.html', context)


@staff_member_required
def admin_verification_action(request, verification_id):
    """Handle approve/reject action for a specific verification"""
    verification = get_object_or_404(OwnerVerification, id=verification_id)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "approve":
            verification.is_verified = True
            verification.save()
            
            owner_profile = OwnerProfile.objects.filter(user=verification.user).first()
            if owner_profile:
                owner_profile.is_verified = True
                owner_profile.save()
            
            messages.success(request, f"{verification.user.username}'s verification approved!")
            
        elif action == "reject":
            verification.is_verified = False
            verification.document_file = None
            verification.save()
            messages.warning(request, f"{verification.user.username}'s verification rejected.")
        
        return redirect("admin_verification")
    
    return redirect("admin_verification")

