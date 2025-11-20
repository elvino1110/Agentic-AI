"""
Script to populate Lead Analysis Database with sample customer data (360 customers)
"""

from LeadDatabase import LeadAnalysisDatabase
from datetime import datetime, timedelta
import random
import sqlite3

def generate_sample_data():
    """Generate 360 customers with realistic purchase patterns."""

    db = LeadAnalysisDatabase()

    # Sample products (motorcycles)
    products = [
        "Honda CBR 150",
        "Honda Vario 160",
        "Honda PCX 160",
        "Honda ADV 160",
        "Honda Beat",
        "Honda Scoopy",
        "Yamaha NMAX",
        "Yamaha Aerox",
        "Yamaha R15",
        "Suzuki GSX-R150"
    ]

    # Insert products
    print("Inserting products...")
    import sqlite3
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    for product in products:
        try:
            cursor.execute('''
                INSERT INTO PRODUCTS (name, category, price)
                VALUES (?, ?, ?)
            ''', (product, "Motorcycle", random.randint(15000000, 45000000)))
        except sqlite3.IntegrityError:
            pass  # Product already exists
    conn.commit()
    conn.close()

    print(f"Generating 360 customers with purchase history...")

    # Generate 360 customers
    for i in range(1, 361):
        customer_name = f"Customer {i:03d}"
        email = f"customer{i}@email.com"
        phone = f"08{random.randint(10000000000, 99999999999)}"

        # Random number of purchases per customer (1 to 5)
        num_purchases = random.randint(1, 5)

        # Generate purchase history
        current_date = datetime.now()
        previous_purchase_date = None

        for purchase_num in range(num_purchases):
            # Random product
            product = random.choice(products)

            # Calculate purchase date (going backwards in time)
            if purchase_num == 0:
                # Most recent purchase (within last 180 days)
                days_ago = random.randint(1, 180)
            else:
                # Older purchases with realistic buying cycles
                days_ago = days_ago + random.randint(200, 800)  # 200-800 days between purchases

            purchase_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            purchase_amount = random.randint(15000000, 45000000)

            # Insert purchase
            db.insert_customer_purchase(
                customer_name=customer_name,
                email=email,
                phone=phone,
                product_purchased=product,
                purchase_date=purchase_date,
                purchase_amount=purchase_amount,
                previous_purchase_date=previous_purchase_date
            )

            # Update for next iteration
            previous_purchase_date = purchase_date

        if (i % 50) == 0:
            print(f"  Generated {i}/360 customers...")

    print("\n✅ Sample data generation complete!")
    print(f"   Total customers: 360")
    print(f"   Database location: {db.db_name}")

    return db


def generate_leads_from_customers(db):
    """Generate leads from all customers with purchase history."""
    print("\n📊 Generating leads from customer purchase patterns...")

    result = db.generate_all_leads()
    print(f"   {result}")

    # Show statistics
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM LEADS WHERE is_redundant = 0")
    total_leads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM LEADS WHERE interest_level = 'High' AND is_redundant = 0")
    high_interest = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM LEADS WHERE interest_level = 'Medium' AND is_redundant = 0")
    medium_interest = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM LEADS WHERE interest_level = 'Low' AND is_redundant = 0")
    low_interest = cursor.fetchone()[0]

    conn.close()

    print(f"\n📈 Lead Statistics:")
    print(f"   Total Leads: {total_leads}")
    print(f"   High Interest: {high_interest}")
    print(f"   Medium Interest: {medium_interest}")
    print(f"   Low Interest: {low_interest}")


def show_sample_predictions(db):
    """Show sample predictions for a few customers."""
    print("\n🔮 Sample Predictions:")

    import sqlite3
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT customer_name
        FROM CUSTOMER_PROFILE_SALES
        WHERE average_buying_cycle_days IS NOT NULL
        LIMIT 5
    ''')

    customers = [row[0] for row in cursor.fetchall()]
    conn.close()

    for customer in customers:
        prediction = db.predict_next_purchase(customer)
        if prediction:
            print(f"\n   Customer: {prediction['customer_name']}")
            print(f"   Last Purchase: {prediction['last_purchase_date']}")
            print(f"   Buying Cycle: {prediction['purchase_distance_days']} days")
            print(f"   Predicted Next Purchase: {prediction['predicted_next_purchase']}")
            print(f"   Product Interest: {prediction['product_interest']}")


if __name__ == "__main__":
    print("=" * 60)
    print("LEAD ANALYSIS DATABASE - SAMPLE DATA GENERATOR")
    print("=" * 60)

    # Generate customer data
    db = generate_sample_data()

    # Generate leads
    generate_leads_from_customers(db)

    # Show sample predictions
    show_sample_predictions(db)

    print("\n" + "=" * 60)
    print("✅ COMPLETE! Database ready for Lead Analysis Agent")
    print("=" * 60)
