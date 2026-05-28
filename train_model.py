import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import warnings

# Suppress minor warnings for a clean output
warnings.filterwarnings('ignore')


def train_credit_model():
    print("📊 Loading merchant_training_data.csv...")
    try:
        df = pd.read_csv('merchant_training_data.csv')
    except FileNotFoundError:
        print("❌ Error: merchant_training_data.csv not found. Did you run generate_dataset.py?")
        return

    print("⚙️ Engineering financial features for each merchant...")
    merchant_features = []

    # We group all transactions by Merchant to summarize their financial health
    for merchant_id, group in df.groupby('Merchant_ID'):
        # Sum up all Credits (Revenue) and Debits (Expenses)
        total_revenue = group[group['Transaction_Type']
                              == 'Credit']['Amount_NGN'].sum()
        total_expenses = group[group['Transaction_Type']
                               == 'Debit']['Amount_NGN'].sum()

        # Calculate Net Profit and Transaction Volume
        net_profit = total_revenue - total_expenses
        transaction_count = len(group)

        # The answer key we generated earlier (1 = Healthy, 0 = Struggling)
        risk_label = group['Risk_Profile_Label'].iloc[0]

        merchant_features.append({
            'Merchant_ID': merchant_id,
            'Total_Revenue': total_revenue,
            'Total_Expenses': total_expenses,
            'Net_Profit': net_profit,
            'Transaction_Count': transaction_count,
            'Risk_Label': risk_label
        })

    # Convert our grouped data into a new DataFrame
    features_df = pd.DataFrame(merchant_features)

    # Define our Inputs (X) and our Output/Answer (y)
    X = features_df[['Total_Revenue', 'Total_Expenses',
                     'Net_Profit', 'Transaction_Count']]
    y = features_df['Risk_Label']

    # Split the data: 80% to train the model, 20% to test its accuracy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    print("🧠 Training the Random Forest AI model...")
    # We use a Random Forest with 100 decision trees
    model = RandomForestClassifier(
        n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)

    print("🔍 Evaluating model accuracy on test data...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred) * 100

    print(f"\n======================================")
    print(f"✅ Model Accuracy: {accuracy:.2f}%")
    print(f"======================================\n")
    print("Detailed Report:")
    print(classification_report(y_test, y_pred,
          target_names=["High Risk (0)", "Low Risk (1)"]))

    # Save the trained model to a file so Django can use it
    model_filename = 'credit_scoring_model.pkl'
    joblib.dump(model, model_filename)
    print(f"💾 Model successfully saved to {model_filename}!")
    print("Next step: Plug this into Django!")


if __name__ == "__main__":
    train_credit_model()
