"""
Custom User model for Handwritten Notes Digitizer.

Two roles exist:
  - ADMIN    : platform administrators (manage accounts & content)
  - CUSTOMER : end users who upload handwritten documents
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("account_status", User.AccountStatus.APPROVED)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


def profile_picture_path(instance, filename):
    return f"profiles/{instance.pk}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    """
    Single user model for both Admin and Customer roles.
    New customer registrations start as PENDING and must be approved by an Admin.
    """

    class Role(models.TextChoices):
        ADMIN    = "admin",    "Admin"
        CUSTOMER = "customer", "Customer"

    class AccountStatus(models.TextChoices):
        PENDING  = "pending",  "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED= "suspended","Suspended"

    # ── Identity ──────────────────────────────────────────────────────────────
    email        = models.EmailField(unique=True)
    first_name   = models.CharField(max_length=100)
    last_name    = models.CharField(max_length=100)
    phone        = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to=profile_picture_path, null=True, blank=True
    )

    # ── Role & Status ─────────────────────────────────────────────────────────
    role           = models.CharField(
        max_length=10, choices=Role.choices, default=Role.CUSTOMER
    )
    account_status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
        help_text="Customer accounts must be approved by an admin before login.",
    )

    # ── Django permission flags ───────────────────────────────────────────────
    is_staff  = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at  = models.DateTimeField(auto_now=True)

    # ── Admin notes ───────────────────────────────────────────────────────────
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes written by admins when approving/rejecting accounts.",
    )

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name      = "User"
        verbose_name_plural = "Users"
        ordering          = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}> [{self.role}]"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_approved(self):
        return self.account_status == self.AccountStatus.APPROVED

    def approve(self, notes=""):
        self.account_status = self.AccountStatus.APPROVED
        if notes:
            self.admin_notes = notes
        self.save(update_fields=["account_status", "admin_notes", "updated_at"])

    def reject(self, notes=""):
        self.account_status = self.AccountStatus.REJECTED
        if notes:
            self.admin_notes = notes
        self.save(update_fields=["account_status", "admin_notes", "updated_at"])
