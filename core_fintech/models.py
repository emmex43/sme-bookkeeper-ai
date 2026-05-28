from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class MerchantProfile(models.Model):
    """
    Profile for SME business owners mapping to the base User model.
    """
    # Use AUTH_USER_MODEL for scalable user management
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchant_profile'
    )
    business_name = models.CharField(max_length=255, db_index=True)
    business_type = models.CharField(max_length=150)

    # OPay Wallet ID might be uniquely identifying, hence unique=True (or at least indexed)
    opay_wallet_id = models.CharField(
        max_length=50, blank=True, null=True, unique=True)
    credit_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Merchant Profile'
        verbose_name_plural = 'Merchant Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business_name} ({self.user.username})"


class LedgerEntry(models.Model):
    """
    Records all individual financial transactions (credits/debits) for a merchant.
    """
    class TransactionType(models.TextChoices):
        CREDIT = 'CR', 'Credit'
        DEBIT = 'DR', 'Debit'

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    transaction_type = models.CharField(
        max_length=2,
        choices=TransactionType.choices
    )
    # 12 digits allows up to 9,999,999,999.99 - scale as needed
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Using timezone.now instead of auto_now_add allows for backdating entries if required
    transaction_date = models.DateTimeField(
        default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'
        # Order by newest transactions first
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.merchant.business_name} - {self.get_transaction_type_display()} - ₦{self.amount}"


class LoanApplication(models.Model):
    """
    Tracks loan requests from merchants and AI-driven credit analysis.
    """
    class LoanStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name='loan_applications'
    )
    amount_requested = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        # Example minimum loan amount
        validators=[MinValueValidator(Decimal('100.00'))]
    )
    status = models.CharField(
        max_length=10,
        choices=LoanStatus.choices,
        default=LoanStatus.PENDING,
        db_index=True
    )

    # TextField to store structured or unstructured AI analysis text/JSON
    gemini_analysis = models.TextField(
        blank=True,
        help_text="Stores the AI evaluation and reasoning for the credit decision."
    )

    application_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'
        ordering = ['-application_date']

    def __str__(self):
        return f"Loan: {self.merchant.business_name} - ₦{self.amount_requested} ({self.status})"
