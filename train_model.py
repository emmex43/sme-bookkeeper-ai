"""
SME Bookkeeper — Credit Score ML Model Trainer
===============================================
Trains a Random Forest REGRESSOR (not classifier) to predict a
continuous credit score (300–850) from 8 engineered merchant features.

Run:  python train_model.py
Out:  credit_scoring_model.pkl  +  feature_names.pkl

Features used:
  1. total_revenue          — sum of all credit entries
  2. total_expenses         — sum of all debit entries
  3. net_profit             — revenue - expenses
  4. revenue_expense_ratio  — revenue / (expenses + 1)
  5. expense_ratio          — expenses / (revenue + 1)  [cost burden]
  6. credit_debit_ratio     — credit count / (debit count + 1)
  7. avg_transaction_value  — mean credit entry amount
  8. round_number_ratio     — % of entries that are suspiciously round
                              (fraud signal)
"""

import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

FEATURE_COLS = [
    'total_revenue',
    'total_expenses',
    'net_profit',
    'revenue_expense_ratio',
    'expense_ratio',
    'credit_debit_ratio',
    'avg_transaction_value',
    'round_number_ratio',
]


def _is_round(amount: float) -> bool:
    """Returns True if amount is a suspiciously round number (fabrication signal)."""
    return amount % 1000 == 0 or amount % 500 == 0


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates raw transaction rows into one feature row per merchant.
    This is the same aggregation Django will run at score time.
    """
    records = []

    for merchant_id, group in df.groupby('Merchant_ID'):
        credits = group[group['Transaction_Type'] == 'Credit']
        debits  = group[group['Transaction_Type'] == 'Debit']

        total_revenue  = credits['Amount_NGN'].sum()
        total_expenses = debits['Amount_NGN'].sum()
        net_profit     = total_revenue - total_expenses
        credit_count   = len(credits)
        debit_count    = len(debits)

        revenue_expense_ratio = total_revenue / (total_expenses + 1)
        expense_ratio         = total_expenses / (total_revenue + 1)
        credit_debit_ratio    = credit_count / (debit_count + 1)
        avg_transaction_value = credits['Amount_NGN'].mean() if credit_count > 0 else 0
        round_number_ratio    = group['Amount_NGN'].apply(_is_round).mean()

        # Target: the continuous score we generated (300–850)
        target_score = group['Target_Score'].iloc[0]

        records.append({
            'Merchant_ID':          merchant_id,
            'total_revenue':        total_revenue,
            'total_expenses':       total_expenses,
            'net_profit':           net_profit,
            'revenue_expense_ratio': revenue_expense_ratio,
            'expense_ratio':        expense_ratio,
            'credit_debit_ratio':   credit_debit_ratio,
            'avg_transaction_value': avg_transaction_value,
            'round_number_ratio':   round_number_ratio,
            'target_score':         target_score,
        })

    return pd.DataFrame(records)


def train_credit_model():
    print("📊 Loading merchant_training_data.csv...")
    try:
        df = pd.read_csv('merchant_training_data.csv')
    except FileNotFoundError:
        print("❌ merchant_training_data.csv not found. Run generate_dataset.py first.")
        return

    print(f"   Loaded {len(df):,} rows for {df['Merchant_ID'].nunique()} merchants.")

    print("⚙️  Engineering 8 features per merchant...")
    features_df = engineer_features(df)

    X = features_df[FEATURE_COLS]
    y = features_df['target_score']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("🧠 Training Gradient Boosting Regressor...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model',  GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )),
    ])
    pipeline.fit(X_train, y_train)

    # -------------------------------------------------------------------
    # Evaluation
    # -------------------------------------------------------------------
    y_pred = pipeline.predict(X_test)
    y_pred_clipped = np.clip(y_pred, 300, 850).round().astype(int)

    mae = mean_absolute_error(y_test, y_pred_clipped)
    r2  = r2_score(y_test, y_pred_clipped)

    # Cross-validation on full dataset for robust estimate
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='r2')

    print(f"\n{'='*45}")
    print(f"  Mean Absolute Error : {mae:.1f} score points")
    print(f"  R² Score            : {r2:.4f}")
    print(f"  Cross-Val R² (5-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"{'='*45}")

    # Feature importance
    importances = pipeline.named_steps['model'].feature_importances_
    print("\n📌 Feature Importances:")
    for feat, imp in sorted(zip(FEATURE_COLS, importances), key=lambda x: -x[1]):
        bar = '█' * int(imp * 40)
        print(f"  {feat:<25} {bar} {imp:.3f}")

    # Sample predictions
    print("\n🔍 Sample Predictions (first 5 test merchants):")
    print(f"  {'Actual':>8}  {'Predicted':>9}")
    for actual, pred in list(zip(y_test.values, y_pred_clipped))[:5]:
        print(f"  {actual:>8}  {pred:>9}")

    # -------------------------------------------------------------------
    # Save model + feature names (Django needs both)
    # -------------------------------------------------------------------
    joblib.dump(pipeline,    'credit_scoring_model.pkl')
    joblib.dump(FEATURE_COLS, 'feature_names.pkl')

    print("\n💾 Saved → credit_scoring_model.pkl")
    print("💾 Saved → feature_names.pkl")
    print("\n✅ Next step: copy both .pkl files into core_fintech/ and update utils.py")


if __name__ == '__main__':
    train_credit_model()