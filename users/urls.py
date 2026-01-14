#users urls
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Forgot Password Flow
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # dashboards

    path('dashboard/superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('dashboard/studentadmin/', views.student_admin_dashboard, name='student_admin_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    # profile view 
    path('profile/', views.profile_view, name='profile'),
    path('users/<int:user_id>/profile/', views.profile_view, name='view_user_profile'),

]
