# CreditSync 🇳🇬
### AI-Powered Credit Scoring & Financial Management for Nigerian SMEs

[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![ML Model](https://img.shields.io/badge/ML-Gradient%20Boosting-orange)](https://scikit-learn.org)
[![AI](https://img.shields.io/badge/AI-Gemini%203.5%20Flash-purple)](https://ai.google.dev)

---

## The Problem

Over **40 million Nigerian SMEs** have no access to formal credit — not because they aren't profitable, but because they have no verifiable financial history. Banks demand records. Merchants have WhatsApp notes.

**CreditSync bridges that gap.**

---

## What It Does

CreditSync is a mobile-first web application that turns a merchant's daily sales and expenses into a **verified, ML-powered credit score** — and uses that score to make instant AI loan decisions.

| Feature | Description |
|---|---|
| 📒 **Digital Ledger** | Log sales and expenses from any phone browser |
| 🤖 **ML Credit Scoring** | Gradient Boosting model trained on 120,000 Nigerian SME transactions |
| 🛡️ **Fraud Detection** | Penalises backdated entries and round-number fabrication automatically |
| 💡 **AI Financial Advisor** | Gemini 3.5 Flash generates 3-sentence actionable weekly insights |
| 💰 **Instant Loan Decisions** | AI evaluates credit score and revenue to approve or decline in seconds |
| 🔐 **Multi-merchant Auth** | Each merchant sees only their own isolated data |

---

## Credit Score Range

```
300 ────────────────────────────────── 850
│         │           │          │       │
Poor    Fair       Average     Good  Excellent
300-439  440-579   550-649   650-749  750-850
```

The score updates automatically every time a new transaction is logged.

---

## Fraud Detection

CreditSync penalises two patterns that indicate fabricated data:

**1. Round Number Ratio** — Real business data has irregular amounts (₦47,500, ₦13,750).
If more than 60% of a merchant's transactions are round thousands, the score is penalised up to 80 points.

**2. Entry Velocity** — Real merchants log transactions throughout the month.
If 70%+ of entries appear in the last 14 days just before a loan application, the score is penalised as a backdating signal.

---

## Tech Stack

```
Backend:     Django 5.2 + Python 3.13
Database:    PostgreSQL (Supabase)
ML Model:    Scikit-learn Gradient Boosting Regressor
AI Advisor:  Google Gemini 3.5 Flash (google-genai SDK)
Frontend:    Tailwind CSS (mobile-first, no framework)
Deployment:  Render
Auth:        Django built-in session authentication
```

---

## ML Model Performance

```
Training data:   120,000 transactions across 600 merchants
MAE:             7.4 score points
R² Score:        0.9971
CV R² (5-fold):  0.9973 ± 0.0006
Score range:     300 – 816
```

Feature importance:
```
total_expenses            34.6%
avg_transaction_value     27.1%
revenue_expense_ratio     16.3%
net_profit                15.4%
expense_ratio              3.2%
credit_debit_ratio         1.5%
round_number_ratio         0.2%  ← fraud signal
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL database (Supabase free tier works)
- Google Gemini API key (get one free at aistudio.google.com/apikey)

### Installation

```bash
# Clone the repository
git clone https://github.com/emmex43/sme-bookkeeper-ai.git
cd sme-bookkeeper-ai

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root — never commit this file:

```
SECRET_KEY=your-django-secret-key
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Run the Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 — register as a merchant and start logging transactions.

---

## How It Works

```
Merchant registers
        ↓
Logs daily sales and expenses
        ↓
Signal fires on every new entry
        ↓
ML model extracts 8 features from ledger history
        ↓
Fraud penalties applied (round numbers, velocity)
        ↓
Credit score updated (300-850)
        ↓
Gemini AI analyses 7-day summary
        ↓
Actionable financial advice generated
        ↓
Merchant applies for loan
        ↓
AI approves or declines with reasoning
```

---

## Project Structure

```
creditsync/
├── core_fintech/
│   ├── models.py                    # MerchantProfile, LedgerEntry, LoanApplication
│   ├── views.py                     # Dashboard, auth, loan, ledger views
│   ├── utils.py                     # ML credit scoring engine
│   ├── ai_services.py               # Gemini AI advisor integration
│   ├── signals.py                   # Auto-triggers score recalculation
│   ├── forms.py                     # Ledger and registration forms
│   ├── admin.py                     # Django admin configuration
│   ├── credit_scoring_model.pkl     # Trained Gradient Boosting model
│   ├── feature_names.pkl            # Feature order for inference
│   └── templates/
│       └── core_fintech/
│           ├── base.html            # Tailwind config, shared layout
│           ├── dashboard.html       # Main merchant dashboard
│           ├── login.html           # Login page
│           ├── register.html        # Merchant registration
│           ├── log_entry.html       # Log sale / expense form
│           ├── ledger_list.html     # Full transaction history
│           └── loan_application.html # AI loan decision page
├── sme_project/
│   ├── settings.py
│   └── urls.py
├── requirements.txt
└── manage.py
```

---

## Roadmap

- [ ] File upload bulk import (CSV/Excel ledger files)
- [ ] OPay API transaction verification
- [ ] Lender dashboard for credit report access
- [ ] WhatsApp bot for transaction logging
- [ ] React Native mobile app
- [ ] Multi-language support (Yoruba, Igbo, Hausa)

---

## The Vision

CreditSync is not just a bookkeeping app. It is infrastructure for financial inclusion — a system that makes the daily activity of running a Nigerian small business the foundation of a credible credit identity.

Every sale logged. Every expense recorded. Every naira tracked.

**That is your credit score. That is your access to capital.**

---

## Built For

- Hackaholics 7.0 — Wema Bank Fintech Hackathon
- Nigerian SME merchants with no formal credit history
- Lenders who need verifiable data, not self-reported forms

---

## Author

**Emmanuel Akhabue**
Chemical Engineering student, University of Benin
Full-stack developer | ML practitioner | Fintech builder

GitHub: https://github.com/emmex43
Email: akhabueemmanuel43@gmail.com

---

## License

MIT License — feel free to fork, improve, and build on this.

---

*"Access to credit is not a privilege. For Nigerian SMEs, it should be infrastructure."*
