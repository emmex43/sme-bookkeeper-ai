from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import LedgerEntry, MerchantProfile


# ---------------------------------------------------------------------------
# Auth Forms
# ---------------------------------------------------------------------------

class MerchantRegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm with business fields.
    On save, creates both a User and a linked MerchantProfile.
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
        'placeholder': 'your@email.com',
    }))
    business_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
        'placeholder': 'e.g. Adaeze Foods & Supplies',
    }))
    business_type = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
        'placeholder': 'e.g. Food & Beverage, Retail, Fashion',
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'business_name',
                  'business_type', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent Tailwind styling to all inherited fields
        input_class = 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base'
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs['class'] = input_class
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password'
        # Remove verbose help texts for cleaner mobile UI
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create the linked MerchantProfile immediately after user creation
            MerchantProfile.objects.create(
                user=user,
                business_name=self.cleaned_data['business_name'],
                business_type=self.cleaned_data['business_type'],
            )
        return user


# ---------------------------------------------------------------------------
# Ledger Entry Form (unchanged, kept here for single import source)
# ---------------------------------------------------------------------------

class LedgerEntryForm(forms.ModelForm):

    class Meta:
        model = LedgerEntry
        fields = ['amount', 'category', 'description', 'transaction_date']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
            }),
            'category': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
                'placeholder': 'e.g. Food Sales, Rent, Inventory',
                'list': 'category-suggestions',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base resize-none',
                'placeholder': 'Optional note about this transaction...',
                'rows': 3,
            }),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand text-base',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'amount': 'Amount (₦)',
            'category': 'Category',
            'description': 'Description',
            'transaction_date': 'Date & Time',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('transaction_date'):
            from django.utils import timezone
            self.initial['transaction_date'] = timezone.now().strftime(
                '%Y-%m-%dT%H:%M')
        self.fields['description'].required = False
