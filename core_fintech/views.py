from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone

from .ai_services import FintechAIService
from .forms import LedgerEntryForm, MerchantRegisterForm
from .models import LedgerEntry, MerchantProfile


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------

def register_view(request):
    """New merchant signup — creates User + MerchantProfile in one step."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = MerchantRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CreditSyn{user.merchant_profile.business_name}!")
            return redirect('dashboard')
    else:
        form = MerchantRegisterForm()

    return render(request, 'core_fintech/register.html', {'form': form})


def login_view(request):
    """Standard username/password login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Respect ?next= parameter so protected redirects work
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'core_fintech/login.html', {'form': form})


def logout_view(request):
    """POST-only logout for CSRF safety."""
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def merchant_dashboard(request):
    """
    Uses request.user instead of .first() — each merchant sees only
    their own data.
    """
    try:
        merchant = request.user.merchant_profile
    except MerchantProfile.DoesNotExist:
        # Edge case: logged-in user has no merchant profile yet
        messages.warning(request, "Please complete your merchant profile.")
        return redirect('register')

    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_entries = LedgerEntry.objects.filter(
        merchant=merchant
    ).order_by('-transaction_date')[:5]

    recent_30 = LedgerEntry.objects.filter(
        merchant=merchant,
        transaction_date__gte=thirty_days_ago,
    )
    total_revenue = (
        recent_30.filter(transaction_type=LedgerEntry.TransactionType.CREDIT)
        .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )
    total_expenses = (
        recent_30.filter(transaction_type=LedgerEntry.TransactionType.DEBIT)
        .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )

    raw_score = merchant.credit_score or 300
    score_percentage = int(((raw_score - 300) / 550) * 100)
    score_percentage = max(0, min(score_percentage, 100))

    gemini_advice = FintechAIService.generate_financial_advice(merchant.id)
    print(f"ADVICE LENGTH: {len(gemini_advice)} chars")

    print(f"ADVICE: {gemini_advice}")

    return render(request, 'core_fintech/dashboard.html', {
        'merchant': merchant,
        'recent_entries': recent_entries,
        'gemini_advice': gemini_advice,
        'score_percentage': score_percentage,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
    })


# ---------------------------------------------------------------------------
# Ledger entry views
# ---------------------------------------------------------------------------

def _get_merchant_or_redirect(request):
    """Helper — returns merchant or None if profile missing."""
    try:
        return request.user.merchant_profile
    except MerchantProfile.DoesNotExist:
        return None


@login_required
def log_sale(request):
    merchant = _get_merchant_or_redirect(request)
    if not merchant:
        return redirect('register')

    if request.method == 'POST':
        form = LedgerEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.merchant = merchant
            entry.transaction_type = LedgerEntry.TransactionType.CREDIT
            entry.save()
            messages.success(request, "Sale logged successfully!")
            return redirect('dashboard')
    else:
        form = LedgerEntryForm()

    return render(request, 'core_fintech/log_entry.html', {
        'form': form,
        'merchant': merchant,
        'entry_type': 'sale',
        'title': 'Log a Sale',
        'subtitle': 'Record money coming into your business',
        'button_label': 'Save Sale',
    })


@login_required
def log_expense(request):
    merchant = _get_merchant_or_redirect(request)
    if not merchant:
        return redirect('register')

    if request.method == 'POST':
        form = LedgerEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.merchant = merchant
            entry.transaction_type = LedgerEntry.TransactionType.DEBIT
            entry.save()
            messages.success(request, "Expense logged successfully!")
            return redirect('dashboard')
    else:
        form = LedgerEntryForm()

    return render(request, 'core_fintech/log_entry.html', {
        'form': form,
        'merchant': merchant,
        'entry_type': 'expense',
        'title': 'Log an Expense',
        'subtitle': 'Record money going out of your business',
        'button_label': 'Save Expense',
    })


@login_required
def ledger_list(request):
    """View to show the full history of transactions."""

    # FIXED: Added the underscore to match your database!
    merchant = request.user.merchant_profile

    # Fetch ALL transactions, ordered by newest first
    all_entries = LedgerEntry.objects.filter(
        merchant=merchant
    ).order_by('-transaction_date')

    context = {
        'merchant': merchant,
        'entries': all_entries,
    }
    return render(request, 'core_fintech/ledger_list.html', context)


@login_required
def loan_application(request):
    """Handles the loan application form and displays the AI's decision."""
    merchant = request.user.merchant_profile
    context = {'merchant': merchant}

    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            requested_amount = float(amount_str)
            if requested_amount <= 0:
                raise ValueError

            # 🚀 Call the AI to evaluate the loan!
            ai_decision = FintechAIService.evaluate_loan(
                merchant.id, requested_amount)

            context['requested_amount'] = requested_amount
            context['decision'] = ai_decision

        except (ValueError, TypeError):
            context['error'] = "Please enter a valid loan amount."

    return render(request, 'core_fintech/loan_application.html', context)
