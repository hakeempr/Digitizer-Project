"""
Accounts views: registration, login, logout, profile management.
"""

from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Open endpoint — new customers self-register.
    Account is created in PENDING state until an admin approves it.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": (
                    "Registration successful. Your account is pending admin approval. "
                    "You will be notified once it is reviewed."
                ),
                "user_id": user.pk,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Returns a DRF Token on success.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "email": user.email,
                "role": user.role,
                "full_name": user.get_full_name(),
            }
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Deletes the current auth token (server-side logout).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully."})


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/profile/  — retrieve own profile
    PUT  /api/v1/auth/profile/  — update own profile
    PATCH /api/v1/auth/profile/ — partial update
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Authenticated user changes their own password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Invalidate existing token so user must re-login
        request.user.auth_token.delete()
        return Response(
            {"message": "Password changed successfully. Please log in again."}
        )
