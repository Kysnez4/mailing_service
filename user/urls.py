#users
from django.urls import path
from .views import RegisterView, CustomUserLogin, CustomUserLogout, confirm_email, user_list, block_user, disable_mailings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomUserLogin.as_view(), name='login'),
    path('logout/', CustomUserLogout.as_view(), name='logout'),
    path('confirm-email/<str:token>/', confirm_email, name='confirm_email'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    path('users/', user_list, name='user_list'),
    path('users/<int:user_id>/block/', block_user, name='block_user'),
    path('users/<int:user_id>/disable-mailings/', disable_mailings, name='disable_mailings'),
]