"""URL routes for the accounts app."""

from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
)

urlpatterns = [
    path("register/",        RegisterView.as_view(),       name="auth-register"),
    path("login/",           LoginView.as_view(),           name="auth-login"),
    path("logout/",          LogoutView.as_view(),          name="auth-logout"),
    path("profile/",         ProfileView.as_view(),         name="auth-profile"),
    path("change-password/", ChangePasswordView.as_view(),  name="auth-change-password"),
]
