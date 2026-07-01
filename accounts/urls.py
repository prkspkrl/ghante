from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='account_dashboard'),
    path('profile/', views.profile, name='account_profile'),
    path('change-password/', views.change_password, name='account_change_password'),
    path('verify-email/<token>/', views.verify_email, name='verify_email'),
    path('send-phone-verification/', views.send_phone_verification, name='send_phone_verification'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            success_url='/accounts/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/reset/done/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),
]
