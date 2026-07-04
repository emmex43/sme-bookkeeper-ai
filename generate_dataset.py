"""
SME Bookkeeper — Synthetic Training Data Generator
====================================================
Generates 500 merchants × 200 entries = 100,000 rows of realistic
Nigerian SME ledger data with 4 risk tiers and 8 engineered features.

Run:  python generate_dataset.py
Out:  merchant_training_data.csv
"""

import random
from datetime import timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_MERCHANTS = 500
ENTRIES_PER_MERCHANT = 200
LOOKBACK_DAYS = 90

# Nigerian SME transaction categories
CREDIT_CATEGORIES = [
    'Product Sales', 'Wholesale Order', 'Service Rendered',
    'Consultation Fee', 'Online Sales', 'Catering', 'Retail',
]
DEBIT_CATEGORIES = [
    'Inventory Restocking', 'Transport & Fuel', 'Rent',
    'Utilities (Power/Data)', 'Marketing', 'Staff Salary',
    'Equipment Maintenance', 'Food & Refreshment',
]

# Risk tier definitions — maps to a final continuous score band
RISK_TIERS = {
    'Excellent':   {'weight': 0.20, 'credit_ratio': 0.80, 'rev_range': (80000,  500000), 'exp_range': (5000,   60000),  'score_band': (750, 850)},
    'Good':        {'weight': 0.30, 'credit_ratio': 0.65, 'rev_range': (30000,  200000), 'exp_range': (10000,  80000),  'score_band': (600, 749)},
    'Fair':        {'weight': 0.30, 'credit_ratio': 0.50, 'rev_range': (10000,  80000),  'exp_range': (15000,  100000), 'score_band': (450, 599)},
    'Poor':        {'weight': 0.20, 'credit_ratio': 0.35, 'rev_range': (1000,   40000),  'exp_range': (20000,  150000), 'score_band': (300, 449)},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assign_tier() -> str:
    """Randomly assigns a risk tier weighted by realistic market distribution."""
    tiers = list(RISK_TIERS.keys())
    weights = [RISK_TIERS[t]['weight'] for t in tiers]
    return random.choices(tiers, weights=weights, k=1)[0]


def _add_fraud_signals(entries: list, tier: str) -> list:
    """
    Injects realistic fraud patterns into Poor-tier merchants:
    - Round-number clustering (fabricated entries)
    - Entry velocity spikes (backdating before loan application)
    """
    if tier != 'Poor':
        return entries

    # 40% of Poor merchants have fraud signals
    if random.random() > 0.40:
        return entries

    end_date = pd.Timestamp.now()
    spike_date = end_date - timedelta(days=random.randint(1, 7))

    # Add 10-20 backdated round-number credit entries
    for _ in range(random.randint(10, 20)):
        entries.append({
            'Transaction_Date': spike_date - timedelta(minutes=random.randint(1, 30)),
            'Transaction_Type': 'Credit',
            'Category': random.choice(CREDIT_CATEGORIES),
            'Amount_NGN': float(random.choice([50000, 100000, 200000, 500000])),
            'Is_Backdated_Spike': 1,
        })

    return entries


def generate_dataset():
    end_date = pd.Timestamp.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    all_rows = []

    print(f"Generating {NUM_MERCHANTS} merchants × {ENTRIES_PER_MERCHANT} entries...")

    for i in range(1, NUM_MERCHANTS + 1):
        merchant_id = f"MERCH_{str(i).zfill(3)}"
        tier = _assign_tier()
        config = RISK_TIERS[tier]
        target_score = random.randint(*config['score_band'])

        entries = []
        credit_count = 0
        debit_count = 0

        for _ in range(ENTRIES_PER_MERCHANT):
            # Randomise date — not uniformly distributed to mimic real usage
            days_ago = random.expovariate(1 / 30)  # more recent = more likely
            days_ago = min(days_ago, LOOKBACK_DAYS - 1)
            txn_date = end_date - timedelta(days=days_ago,
                                            hours=random.randint(0, 23),
                                            minutes=random.randint(0, 59))

            is_credit = random.random() < config['credit_ratio']

            if is_credit:
                credit_count += 1
                amount = round(random.uniform(*config['rev_range']), 2)
                category = random.choice(CREDIT_CATEGORIES)
                txn_type = 'Credit'
            else:
                debit_count += 1
                amount = round(random.uniform(*config['exp_range']), 2)
                category = random.choice(DEBIT_CATEGORIES)
                txn_type = 'Debit'

            entries.append({
                'Transaction_Date': txn_date,
                'Transaction_Type': txn_type,
                'Category': category,
                'Amount_NGN': amount,
                'Is_Backdated_Spike': 0,
            })

        # Inject fraud signals for some poor-tier merchants
        entries = _add_fraud_signals(entries, tier)

        for entry in entries:
            all_rows.append({
                'Merchant_ID': merchant_id,
                'Risk_Tier': tier,
                'Target_Score': target_score,
                **entry,
            })

    df = pd.DataFrame(all_rows)
    df = df.sort_values(['Merchant_ID', 'Transaction_Date']).reset_index(drop=True)
    df.to_csv('merchant_training_data.csv', index=False)

    print(f"✅ Generated {len(df):,} rows across {NUM_MERCHANTS} merchants.")
    print(f"   Tier distribution:\n{df.groupby('Merchant_ID')['Risk_Tier'].first().value_counts()}")
    print(f"💾 Saved → merchant_training_data.csv")


if __name__ == '__main__':
    generate_dataset()