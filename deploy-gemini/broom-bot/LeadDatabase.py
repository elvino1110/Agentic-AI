# Import necessary libraries
import sqlite3
from datetime import datetime, timedelta
import os


class LeadAnalysisDatabase:
    """Database handler for Lead Analysis and Customer Analytics System."""

    def __init__(self, db_name: str = "lead_analysis.sqlite"):
        """
        Initialize the Lead Analysis Database.

        Args:
            db_name: Name of the SQLite database file (default: "lead_analysis.sqlite")
        """
        # Get the path to the same folder as this file (broom-bot folder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_name = os.path.join(current_dir, db_name)
        self.create_tables()

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create 'customer_profile_sales' table
        create_customer_profile_sales = '''
            CREATE TABLE IF NOT EXISTS CUSTOMER_PROFILE_SALES (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                product_purchased TEXT NOT NULL,
                purchase_date DATE NOT NULL,
                purchase_amount REAL,
                previous_purchase_date DATE,
                purchase_distance_days INTEGER,
                total_purchases INTEGER DEFAULT 1,
                average_buying_cycle_days REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        cursor.execute(create_customer_profile_sales)
        conn.commit()

        # Create 'leads' table
        create_leads_table = '''
            CREATE TABLE IF NOT EXISTS LEADS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                product_interest TEXT NOT NULL,
                last_purchase_date DATE,
                predicted_next_purchase DATE,
                purchase_distance_days INTEGER,
                interest_level TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'New',
                source TEXT DEFAULT 'Predictive Analysis',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                is_redundant INTEGER DEFAULT 0,
                UNIQUE(customer_name, product_interest, predicted_next_purchase)
            )
        '''
        cursor.execute(create_leads_table)
        conn.commit()

        # Create 'products' table for reference
        create_products_table = '''
            CREATE TABLE IF NOT EXISTS PRODUCTS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                price REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        cursor.execute(create_products_table)
        conn.commit()

        conn.close()
        print("Lead Analysis tables created (CUSTOMER_PROFILE_SALES, LEADS, PRODUCTS)")

    # ========================================
    # CUSTOMER PROFILE & SALES METHODS
    # ========================================

    def insert_customer_purchase(self, customer_name, email, phone, product_purchased,
                                  purchase_date, purchase_amount, previous_purchase_date=None):
        """
        Insert a customer purchase record and calculate buying cycle.

        Args:
            customer_name: Customer's full name
            email: Customer's email
            phone: Customer's phone
            product_purchased: Product name
            purchase_date: Purchase date (YYYY-MM-DD)
            purchase_amount: Purchase amount
            previous_purchase_date: Previous purchase date if exists (YYYY-MM-DD)
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Calculate purchase distance if previous purchase exists
        purchase_distance_days = None
        if previous_purchase_date:
            date1 = datetime.strptime(purchase_date, '%Y-%m-%d')
            date2 = datetime.strptime(previous_purchase_date, '%Y-%m-%d')
            purchase_distance_days = abs((date1 - date2).days)

        # Get customer's previous purchases to calculate average buying cycle
        cursor.execute('''
            SELECT purchase_distance_days
            FROM CUSTOMER_PROFILE_SALES
            WHERE customer_name = ? AND purchase_distance_days IS NOT NULL
        ''', (customer_name,))

        previous_distances = [row[0] for row in cursor.fetchall()]

        # Add current distance if exists
        if purchase_distance_days:
            previous_distances.append(purchase_distance_days)

        # Calculate average buying cycle
        average_buying_cycle = None
        if previous_distances:
            average_buying_cycle = sum(previous_distances) / len(previous_distances)

        # Count total purchases
        cursor.execute('SELECT COUNT(*) FROM CUSTOMER_PROFILE_SALES WHERE customer_name = ?', (customer_name,))
        total_purchases = cursor.fetchone()[0] + 1

        # Insert the purchase record
        insert_sql = '''
            INSERT INTO CUSTOMER_PROFILE_SALES
            (customer_name, email, phone, product_purchased, purchase_date, purchase_amount,
             previous_purchase_date, purchase_distance_days, total_purchases, average_buying_cycle_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(insert_sql, (
            customer_name, email, phone, product_purchased, purchase_date, purchase_amount,
            previous_purchase_date, purchase_distance_days, total_purchases, average_buying_cycle
        ))

        connection.commit()
        connection.close()
        print(f"Purchase record added for {customer_name}")

    def calculate_average_buying_cycle(self, customer_name):
        """
        Calculate the average buying cycle for a specific customer.

        Args:
            customer_name: Customer's name

        Returns:
            float: Average buying cycle in days, or None if insufficient data
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute('''
            SELECT average_buying_cycle_days
            FROM CUSTOMER_PROFILE_SALES
            WHERE customer_name = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (customer_name,))

        result = cursor.fetchone()
        connection.close()

        return result[0] if result else None

    def get_customer_last_purchase(self, customer_name):
        """
        Get customer's last purchase information.

        Args:
            customer_name: Customer's name

        Returns:
            dict: Last purchase information
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute('''
            SELECT customer_name, email, phone, product_purchased, purchase_date,
                   purchase_distance_days, average_buying_cycle_days
            FROM CUSTOMER_PROFILE_SALES
            WHERE customer_name = ?
            ORDER BY purchase_date DESC
            LIMIT 1
        ''', (customer_name,))

        row = cursor.fetchone()
        connection.close()

        if row:
            return {
                "customer_name": row[0],
                "email": row[1],
                "phone": row[2],
                "product_purchased": row[3],
                "last_purchase_date": row[4],
                "purchase_distance_days": row[5],
                "average_buying_cycle_days": row[6]
            }
        return None

    # ========================================
    # LEAD PREDICTION & GENERATION METHODS
    # ========================================

    def predict_next_purchase(self, customer_name):
        """
        Predict customer's next purchase date based on buying cycle.

        Args:
            customer_name: Customer's name

        Returns:
            dict: Prediction with next purchase date
        """
        customer_data = self.get_customer_last_purchase(customer_name)

        if not customer_data or not customer_data['average_buying_cycle_days']:
            return None

        # Calculate next purchase date
        last_purchase = datetime.strptime(customer_data['last_purchase_date'], '%Y-%m-%d')
        buying_cycle_days = int(customer_data['average_buying_cycle_days'])
        predicted_next_purchase = last_purchase + timedelta(days=buying_cycle_days)

        return {
            "customer_name": customer_data['customer_name'],
            "email": customer_data['email'],
            "phone": customer_data['phone'],
            "last_purchase_date": customer_data['last_purchase_date'],
            "predicted_next_purchase": predicted_next_purchase.strftime('%Y-%m-%d'),
            "purchase_distance_days": buying_cycle_days,
            "product_interest": customer_data['product_purchased']
        }

    def generate_lead(self, customer_name, check_redundancy=True):
        """
        Generate a lead from customer prediction.

        Args:
            customer_name: Customer's name
            check_redundancy: Check if lead already exists (default: True)

        Returns:
            str: Status message
        """
        prediction = self.predict_next_purchase(customer_name)

        if not prediction:
            return f"Cannot generate lead for {customer_name}: Insufficient purchase history"

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Check for redundant leads
        is_redundant = 0
        if check_redundancy:
            cursor.execute('''
                SELECT id FROM LEADS
                WHERE customer_name = ?
                  AND product_interest = ?
                  AND predicted_next_purchase = ?
            ''', (prediction['customer_name'], prediction['product_interest'], prediction['predicted_next_purchase']))

            if cursor.fetchone():
                is_redundant = 1
                connection.close()
                return f"Lead already exists for {customer_name} (redundant)"

        # Determine interest level based on proximity to predicted date
        today = datetime.now()
        predicted_date = datetime.strptime(prediction['predicted_next_purchase'], '%Y-%m-%d')
        days_until_purchase = (predicted_date - today).days

        if days_until_purchase <= 30:
            interest_level = "High"
        elif days_until_purchase <= 90:
            interest_level = "Medium"
        else:
            interest_level = "Low"

        # Insert lead
        insert_sql = '''
            INSERT INTO LEADS
            (customer_name, email, phone, product_interest, last_purchase_date,
             predicted_next_purchase, purchase_distance_days, interest_level, source, is_redundant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        try:
            cursor.execute(insert_sql, (
                prediction['customer_name'],
                prediction['email'],
                prediction['phone'],
                prediction['product_interest'],
                prediction['last_purchase_date'],
                prediction['predicted_next_purchase'],
                prediction['purchase_distance_days'],
                interest_level,
                'Predictive Analysis',
                is_redundant
            ))
            connection.commit()
            lead_id = cursor.lastrowid
            connection.close()
            return f"Lead generated successfully! ID: {lead_id}, Interest Level: {interest_level}"
        except sqlite3.IntegrityError:
            connection.close()
            return f"Lead already exists for {customer_name} (duplicate detected)"

    def generate_all_leads(self):
        """
        Generate leads for all customers with sufficient purchase history.

        Returns:
            str: Summary of lead generation
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Get all customers with average buying cycle
        cursor.execute('''
            SELECT DISTINCT customer_name
            FROM CUSTOMER_PROFILE_SALES
            WHERE average_buying_cycle_days IS NOT NULL
        ''')

        customers = [row[0] for row in cursor.fetchall()]
        connection.close()

        generated = 0
        redundant = 0
        failed = 0

        for customer in customers:
            result = self.generate_lead(customer, check_redundancy=True)
            if "successfully" in result:
                generated += 1
            elif "redundant" in result or "duplicate" in result:
                redundant += 1
            else:
                failed += 1

        return f"Lead Generation Complete: {generated} new leads, {redundant} redundant, {failed} failed"

    # ========================================
    # QUERY METHODS FOR ANALYSIS
    # ========================================

    def get_leads_by_product(self, product_name, days_range=None):
        """Get leads for a specific product."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        if days_range:
            cursor.execute('''
                SELECT * FROM LEADS
                WHERE product_interest LIKE ?
                  AND created_at >= DATE('now', '-' || ? || ' days')
                  AND is_redundant = 0
                ORDER BY created_at DESC
            ''', (f'%{product_name}%', days_range))
        else:
            cursor.execute('''
                SELECT * FROM LEADS
                WHERE product_interest LIKE ?
                  AND is_redundant = 0
                ORDER BY created_at DESC
            ''', (f'%{product_name}%',))

        results = cursor.fetchall()
        connection.close()
        return results

    def drop_all_tables(self):
        """Drop all tables from the database."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute("DROP TABLE IF EXISTS LEADS")
        cursor.execute("DROP TABLE IF EXISTS CUSTOMER_PROFILE_SALES")
        cursor.execute("DROP TABLE IF EXISTS PRODUCTS")

        connection.commit()
        connection.close()
        print("All lead analysis tables have been dropped.")


# For testing and initialization
if __name__ == "__main__":
    db = LeadAnalysisDatabase()

    print("Lead Analysis Database initialized!")
    print(f"Database location: {db.db_name}")
