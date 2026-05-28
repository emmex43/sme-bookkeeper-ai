# core_fintech/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.merchant_dashboard, name='dashboard'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Ledger
    path('log-sale/', views.log_sale, name='log_sale'),
    path('log-expense/', views.log_expense, name='log_expense'),

    path('ledger/', views.ledger_list, name='ledger_list'),
    path('loan/', views.loan_application, name='loan_application'),
]
