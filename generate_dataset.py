import pandas as pd
import random
from datetime import timedelta
from faker import Faker

# Initialize Faker for realistic data generation
fake = Faker('en_NG')  # Using Nigerian locale for authentic context if needed

NUM_MERCHANTS = 50
TOTAL_ENTRIES = 5000
ENTRIES_PER_MERCHANT = TOTAL_ENTRIES // NUM_MERCHANTS

# Realistic Nigerian SME Categories
CREDIT_CATEGORIES = ['Product Sales', 'Wholesale Order',
                     'Service Rendered', 'Consultation Fee']
DEBIT_CATEGORIES = ['Inventory Restocking', 'Transport & Fuel',
                    'Food & Refreshment', 'Rent', 'Utilities (Power/Data)', 'Marketing']


def generate_dataset():
    data = []

    # Generate 50 unique Merchant IDs
    merchant_ids = [
        f"MERCH_{str(i).zfill(3)}" for i in range(1, NUM_MERCHANTS + 1)]

    # Assign profiles: 35 Healthy, 15 Struggling
    healthy_merchants = set(random.sample(merchant_ids, 35))

    # We span the data over the last 90 days
    end_date = pd.Timestamp.now()
    start_date = end_date - timedelta(days=90)

    print("Generating 5,000 synthetic ledger entries...")

    for merchant_id in merchant_ids:
        # Determine behavior based on profile
        is_healthy = merchant_id in healthy_merchants

        # We generate exactly 100 entries per merchant to hit the 5,000 total
        for _ in range(ENTRIES_PER_MERCHANT):
            # Random date within the 90-day window
            transaction_date = fake.date_time_between(
                start_date=start_date, end_date=end_date)

            if is_healthy:
                # Healthy profile: 70% chance of a sale, 30% chance of an expense
                is_credit = random.random() < 0.7
                if is_credit:
                    transaction_type = 'Credit'
                    category = random.choice(CREDIT_CATEGORIES)
                    # Consistent, decent sales
                    amount = round(random.uniform(5000, 150000), 2)
                else:
                    transaction_type = 'Debit'
                    category = random.choice(DEBIT_CATEGORIES)
                    # Lower controlled expenses
                    amount = round(random.uniform(500, 30000), 2)
            else:
                # Struggling profile: 40% chance of sale, 60% chance of expense
                is_credit = random.random() < 0.4
                if is_credit:
                    transaction_type = 'Credit'
                    category = random.choice(CREDIT_CATEGORIES)
                    # Lower, erratic sales
                    amount = round(random.uniform(500, 40000), 2)
                else:
                    transaction_type = 'Debit'
                    category = random.choice(DEBIT_CATEGORIES)
                    # High, heavy expenses
                    amount = round(random.uniform(10000, 150000), 2)

            data.append({
                'Merchant_ID': merchant_id,
                'Transaction_Date': transaction_date,
                'Transaction_Type': transaction_type,
                'Category': category,
                'Amount_NGN': amount,
                # Useful label for ML later!
                'Risk_Profile_Label': 'Low Risk' if is_healthy else 'High Risk'
            })

    try:
        # Create DataFrame
        df = pd.DataFrame(data)

        # Sort values by Merchant and Date to make it look like a real chronological ledger
        df = df.sort_values(
            by=['Merchant_ID', 'Transaction_Date']).reset_index(drop=True)

        # Export to CSV
        output_filename = "merchant_training_data.csv"
        df.to_csv(output_filename, index=False)
        print(f"✅ Successfully generated dataset with {len(df)} rows.")
        print(f"💾 Saved to: {output_filename}")

        # Display a quick preview in the console
        print("\nData Preview:")
        print(df.head())

    except Exception as e:
        print(f"❌ Error saving dataset: {str(e)}")


if __name__ == "__main__":
    generate_dataset()
