from django.urls import path
from django.contrib.auth import views as auth_views

from task.forms import CustomPasswordResetForm
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path('about/', views.about, name='about'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('buyer/', views.buyer_dashboard, name='buyer_dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path("logout/", views.logout, name="logout"),
    path("verification/", views.verification_page, name='verification_page'),
    path("notification/", views.notifications, name='notifications'),
    path("nearby-listings/", views.nearby_listings, name="nearby_listings"),
    path(
    'forgot_password/',
    auth_views.PasswordResetView.as_view(
        template_name='task/password_reset/forgot_password.html',
        form_class=CustomPasswordResetForm,
        success_url=reverse_lazy('password_reset_done'),
    ),
    name='forgot_password'
),
    path(
        'password-reset-done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='task/password_reset/password_reset_done.html',
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='task/password_reset/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='task/password_reset/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('saved-listings/', views.saved_listings, name='saved_listings'),
    path('report-issue/', views.report_issue, name='report_issue'),
    path('admin-dashboard/', views.admin_view, name='admin_dashboard'),
    path("profile/", views.buyer_profile, name="buyer_profile"),
    path('resolve-report/<int:report_id>/', views.resolve_report, name='resolve_report'),

    path("add-listing-step1/", views.owner_add_listingstep1, name="owner_add_listingstep1"),
    path("add-listing-step2/", views.owner_add_listingstep2, name="owner_add_listingstep2"),
    path("add-listing-step3/", views.owner_add_listingstep3, name="owner_add_listingstep3"),
    path("add-listing-step4/", views.owner_add_listingstep4, name="owner_add_listingstep4"),
    path("show-listings/", views.owner_listing, name="owner_listing"),
    path("owner/listings/<int:pk>/", views.owner_listing_details, name="owner_listing_details"),
    path("owner/listings/<int:pk>/edit/", views.owner_edit_listing, name="owner_edit_listing"),
    path("owner/listings/<int:pk>/submit/", views.submit_listing, name="submit_listing"),

    path("chats/", views.chat_list, name="chat_list"),
    path("chat/start/<int:listing_id>/", views.start_chat, name="start_chat"),
    path("chat/<int:conversation_id>/", views.chat_room, name="chat_room"),
    path("admin-dashboard/listing/<int:listing_id>/", views.admin_listing_detail, name="admin_listing_detail"),
    path("admin-dashboard/listings/", views.admin_listings, name="admin_listings"),
    path("admin-verification/", views.admin_verification, name="admin_verification"),
    path("admin-verification/<int:verification_id>/action/", views.admin_verification_action, name="admin_verification_action"),

    path("buyer/search-room/", views.buyer_search_room, name="buyer_search_room"),
    path('provide-review/', views.provide_review, name='provide_review'),
    path('all-reviews/', views.all_reviews, name='all_reviews'),
    path("buyer/listing/<int:listing_id>/", views.buyer_listing_detail, name="buyer_listing_detail"),
    path("buyer/save/<int:listing_id>/", views.save_listing, name="save_listing"),
    path("buyer/saved/", views.saved_listings, name="saved_listings"),
    
    # Listing Actions
    path('listing/<int:listing_id>/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path("listing/<int:listing_id>/delete/", views.delete_listing, name="delete_listing"),  # Move to trash
    
    # Trash URLs
    path("owner/trash/", views.deleted_listing, name="deleted_listing"),  # View trash page
    path("owner/trash/restore/<int:listing_id>/", views.restore_listing, name="restore_listing"),
    path("owner/trash/permanent-delete/<int:listing_id>/", views.permanent_delete_listing, name="permanent_delete_listing"),
    path("owner/trash/empty/", views.empty_trash, name="empty_trash"),
    path("chatbot/", views.chatbot_api, name="chatbot_api"),
    path("admin-reports/", views.admin_reports, name="admin_reports"),
    path("admin-reports/<int:id>/", views.admin_report_detail, name="admin_report_detail"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)