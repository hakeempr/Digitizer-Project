"""
Signals for the Customer Module.

On new CUSTOMER registration → auto-create an AccountRequest record so
the admin queue is populated immediately.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User


@receiver(post_save, sender=User)
def create_account_request(sender, instance, created, **kwargs):
    """Create an AccountRequest whenever a new Customer account is saved."""
    if created and instance.is_customer:
        from apps.admin_module.models import AccountRequest
        AccountRequest.objects.get_or_create(customer=instance)
