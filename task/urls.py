from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login_view, name='login'),
     path('register/', views.register, name='register'),

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
