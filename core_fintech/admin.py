from django.contrib import admin
from .models import MerchantProfile, LedgerEntry, LoanApplication


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'business_type',
                    'credit_score', 'created_at')
    search_fields = ('business_name', 'user__username', 'opay_wallet_id')
    list_filter = ('business_type', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'transaction_type',
                    'amount', 'category', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date', 'category')
    search_fields = ('merchant__business_name', 'description', 'category')
    date_hierarchy = 'transaction_date'


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'amount_requested',
                    'status', 'application_date')
    list_filter = ('status', 'application_date')
    search_fields = ('merchant__business_name',)
    readonly_fields = ('application_date', 'gemini_analysis')
