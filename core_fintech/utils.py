"""
utils.py
--------
Credit scoring engine using the trained Gradient Boosting Regressor.
Predicts a continuous score (300-850) directly from merchant ledger features.

Features (must match train_model.py exactly):
  1. total_revenue
  2. total_expenses
  3. net_profit
  4. revenue_expense_ratio
  5. expense_ratio
  6. credit_debit_ratio
  7. avg_transaction_value
  8. round_number_ratio
"""

import logging
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd

import joblib
import numpy as np
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Load model once at import time ───────────────────────────────────────────
_BASE_DIR      = Path(__file__).resolve().parent
_MODEL_PATH    = _BASE_DIR / 'credit_scoring_model.pkl'
_FEATURES_PATH = _BASE_DIR / 'feature_names.pkl'

try:
    _model         = joblib.load(_MODEL_PATH)
    _feature_names = joblib.load(_FEATURES_PATH)
    logger.info("Credit scoring model loaded. Features: %s", _feature_names)
except FileNotFoundError as e:
    _model         = None
    _feature_names = None
    logger.warning("Model file not found (%s). Using heuristic fallback.", e)

MIN_SCORE = 300
MAX_SCORE = 850


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_credit_score(merchant_id: int) -> int:
    """
    Called by post_save signal on LedgerEntry.
    Extracts features → runs model → saves score to MerchantProfile.
    Returns integer score in [300, 850].
    """
    from .models import LedgerEntry, MerchantProfile

    try:
        features = _extract_features(merchant_id, LedgerEntry)

        if _model is not None:
            score = _ml_score(features)
        else:
            score = _heuristic_score(features)

        MerchantProfile.objects.filter(pk=merchant_id).update(credit_score=score)
        logger.debug("Merchant %s → credit score %d", merchant_id, score)
        return score

    except Exception:
        logger.exception("calculate_credit_score failed for merchant %s", merchant_id)
        return MIN_SCORE


# ── Feature extraction ────────────────────────────────────────────────────────

def _extract_features(merchant_id: int, LedgerEntry) -> dict:
    """
    Queries last 90 days and returns the 8 features the model was trained on.
    Feature names must exactly match feature_names.pkl.
    """
    ninety_days_ago   = timezone.now() - timedelta(days=90)
    fourteen_days_ago = timezone.now() - timedelta(days=14)

    entries = LedgerEntry.objects.filter(
        merchant_id=merchant_id,
        transaction_date__gte=ninety_days_ago,
    )

    credits = entries.filter(transaction_type=LedgerEntry.TransactionType.CREDIT)
    debits  = entries.filter(transaction_type=LedgerEntry.TransactionType.DEBIT)

    total_revenue  = float(credits.aggregate(t=Sum('amount'))['t'] or 0)
    total_expenses = float(debits.aggregate(t=Sum('amount'))['t'] or 0)
    net_profit     = total_revenue - total_expenses

    credit_count = credits.count()
    debit_count  = debits.count()
    tx_count     = entries.count()

    revenue_expense_ratio = total_revenue / (total_expenses + 1)
    expense_ratio         = total_expenses / (total_revenue + 1)
    credit_debit_ratio    = credit_count / max(debit_count, 1)

    # Average transaction value across ALL entries
    all_amounts = list(entries.values_list('amount', flat=True))
    avg_transaction_value = (
        sum(float(a) for a in all_amounts) / max(len(all_amounts), 1)
    )

    # Round number ratio — fabrication fraud signal
    round_number_ratio = (
        sum(1 for a in all_amounts if float(a) % 1000 == 0)
        / max(len(all_amounts), 1)
    )

    return {
        'total_revenue':          total_revenue,
        'total_expenses':         total_expenses,
        'net_profit':             net_profit,
        'revenue_expense_ratio':  revenue_expense_ratio,
        'expense_ratio':          expense_ratio,
        'credit_debit_ratio':     credit_debit_ratio,
        'avg_transaction_value':  avg_transaction_value,
        'round_number_ratio':     round_number_ratio,
    }


# ── Scoring ───────────────────────────────────────────────────────────────────

def _ml_score(features: dict) -> int:
    """
    Runs the Gradient Boosting Regressor.
    Uses feature_names.pkl to guarantee correct column order.
    """
    X = pd.DataFrame([[features[f] for f in _feature_names]], columns=_feature_names)
    raw_score = float(_model.predict(X)[0])

    # Apply fraud penalty on top of model output
    raw_score = _apply_fraud_penalty(raw_score, features)
    return _clamp(int(round(raw_score)))


def _heuristic_score(features: dict) -> int:
    """Fallback when .pkl files are missing."""
    ratio = min(features['revenue_expense_ratio'], 5.0)
    score = MIN_SCORE + int((ratio / 5.0) * (MAX_SCORE - MIN_SCORE))
    score = _apply_fraud_penalty(score, features)
    return _clamp(score)


def _apply_fraud_penalty(score: float, features: dict) -> float:
    """
    Deducts points for patterns suggesting fabricated data.

    Penalties:
      round_number_ratio > 60%  → up to -80 pts
        (real data has irregular amounts; all-round = suspicious)
    """
    penalty = 0.0

    if features['round_number_ratio'] > 0.60:
        excess   = features['round_number_ratio'] - 0.60
        penalty += excess * 200   # max ~80 pts at 100% round

    return score - penalty


def _clamp(score: int) -> int:
    return max(MIN_SCORE, min(MAX_SCORE, score))