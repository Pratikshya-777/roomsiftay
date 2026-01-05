from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('buyer/', views.buyer, name='buyer-dashboard'),
    path('saved-listings/', views.saved_listings, name='saved_listings'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('report-issue/', views.report_issue, name='report_issue'),
    path('admin-dashboard/', views.admin_view, name='admin_dashboard'),
]
