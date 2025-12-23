from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,contact,about,owner_dashboard,user_dashboard,login_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('owner/', owner_dashboard, name='owner_dashboard'),
    path('user/', user_dashboard, name='user_dashboard'),
    path('login/', login_view, name='login'),
    

    path(
        'forgot-password/',
        auth_views.PasswordResetView.as_view(
            template_name='task/forgot_password.html'
        ),
        name='password_reset'
    ),
    path(
        'password-reset-done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='task/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='task/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='task/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
