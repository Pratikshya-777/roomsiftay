from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path('about/', views.about, name='about'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('buyer/', views.buyer, name='buyer_dashboard'),
    # path('user/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),

    path(
        'forgot_password/',
        auth_views.PasswordResetView.as_view(
            template_name='task/forgot_password.html',
            success_url="/password-reset-done/",
            # email_template_name='task/password_reset_email.html',
            # from_email='RoomSiftay <roomsiftay@gmail.com>',
            # extra_email_context={'domain': '127.0.0.1:8000'}, 
        ),
        name='forgot_password'
    ),

    path(
        'password-reset-done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='task/password_reset_done.html',
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='task/password_reset_confirm.html',
            success_url="/password-reset-complete/",
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='task/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('saved-listings/', views.saved_listings, name='saved_listings'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('report-issue/', views.report_issue, name='report_issue'),
    path('admin-dashboard/', views.admin_view, name='admin_dashboard'),
    path("profile/", views.buyer_profile, name="buyer_profile"),
]


