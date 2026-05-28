from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LedgerEntry


@receiver(post_save, sender=LedgerEntry)
def update_credit_score_on_new_entry(sender, instance, created, **kwargs):
    """
    Fires after every LedgerEntry save.
    Only recalculates the credit score when a new entry is CREATED,
    not on every subsequent edit — avoids redundant recalculations
    when e.g. an admin corrects a description field.
    """
    if created:
        # Import here to avoid circular imports at module load time
        from .utils import calculate_credit_score
        calculate_credit_score(instance.merchant_id)
