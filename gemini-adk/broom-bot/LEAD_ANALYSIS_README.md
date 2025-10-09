# Lead Analysis System - Documentation

## Overview

The **Lead Analysis System** is a predictive lead generation feature that analyzes customer purchase patterns to automatically generate qualified leads.

### How It Works

```
Step 1: Calculate Average Buying Cycle per Customer
        ↓ (from CUSTOMER_PROFILE_SALES table)
Step 2: Predict Next Purchase Date
        ↓ (Last Purchase + Buying Cycle = Predicted Date)
Step 3: Generate Leads & Check Redundancy
        ↓ (Create lead if not duplicate)
Result: Qualified Leads with Interest Levels
```

---

## Database Structure

### Two Separate Databases:

1. **broombot.sqlite** - Booking system (DEALERS, TECHNICIANS, BOOKINGS)
2. **lead_analysis.sqlite** - Lead analysis system (CUSTOMER_PROFILE_SALES, LEADS, PRODUCTS)

---

## Tables

### 1. CUSTOMER_PROFILE_SALES
Stores customer purchase history and calculates buying cycles.

| Column | Type | Description |
|--------|------|-------------|
| customer_name | TEXT | Customer's full name |
| product_purchased | TEXT | Product they bought |
| purchase_date | DATE | When they purchased |
| purchase_distance_days | INTEGER | Days since last purchase |
| average_buying_cycle_days | REAL | Average days between purchases |
| total_purchases | INTEGER | Total number of purchases |

### 2. LEADS
Generated leads based on predictions.

| Column | Type | Description |
|--------|------|-------------|
| customer_name | TEXT | Customer name |
| product_interest | TEXT | Predicted next purchase |
| last_purchase_date | DATE | Their last purchase date |
| predicted_next_purchase | DATE | Predicted next purchase date |
| purchase_distance_days | INTEGER | Their buying cycle |
| interest_level | TEXT | High/Medium/Low |
| is_redundant | INTEGER | 0=unique, 1=duplicate |

---

## Business Logic

### Step 1: Calculate Average Buying Cycle

For each customer, calculate the average number of days between purchases:

```
Customer 001:
- Purchase 1: 2023-01-15
- Purchase 2: 2024-04-20 (460 days later)
- Purchase 3: 2025-08-05 (472 days later)
Average Buying Cycle = (460 + 472) / 2 = 466 days
```

### Step 2: Predict Next Purchase

```
Last Purchase: 2025-08-05
Buying Cycle: 466 days
Predicted Next Purchase = 2025-08-05 + 466 days = 2026-11-14
```

### Step 3: Generate Lead with Interest Level

Based on proximity to predicted date:

- **High Interest**: Predicted purchase within 30 days
- **Medium Interest**: Predicted purchase within 31-90 days
- **Low Interest**: Predicted purchase 90+ days away

### Step 4: Check Redundancy

Before inserting, check if lead already exists:
```sql
SELECT * FROM LEADS
WHERE customer_name = ? AND product_interest = ? AND predicted_next_purchase = ?
```

If exists → Mark as redundant
If not → Insert new lead

---

## Setup & Usage

### 1. Initialize Database

```python
from LeadDatabase import LeadAnalysisDatabase

db = LeadAnalysisDatabase()
# Creates lead_analysis.sqlite with all tables
```

### 2. Populate with Sample Data

```bash
cd gemini-adk/broom-bot
python populate_lead_data.py
```

This will:
- Generate 360 customers
- Create realistic purchase histories (1-5 purchases per customer)
- Calculate buying cycles
- Generate predictive leads
- Show statistics

### 3. Manual Data Entry

```python
# Add a customer purchase
db.insert_customer_purchase(
    customer_name="John Doe",
    email="john@example.com",
    phone="08123456789",
    product_purchased="Honda CBR 150",
    purchase_date="2025-01-15",
    purchase_amount=30000000,
    previous_purchase_date="2023-06-20"  # Optional
)

# Predict next purchase
prediction = db.predict_next_purchase("John Doe")
print(prediction)

# Generate lead
result = db.generate_lead("John Doe", check_redundancy=True)
print(result)
```

### 4. Query Leads

```python
# Get leads for specific product
leads = db.get_leads_by_product("CBR 150", days_range=30)

# Generate all leads
summary = db.generate_all_leads()
```

---

## Agent Integration

The Lead Analysis Agent uses a **SequentialAgent workflow**:

```
Planning Agent → Analyst Agent → Engineer Agent
    ↓                ↓                 ↓
  Strategy    DB Mapping        SQL Execution
```

### Example Queries:

**User:** "Show me high-interest leads for CBR 150"

**Flow:**
1. **Planning Agent**: Creates analysis plan
2. **Analyst Agent**: Maps to database schema
3. **Engineer Agent**: Generates and executes SQL:

```sql
SELECT customer_name, email, phone, predicted_next_purchase, interest_level
FROM LEADS
WHERE product_interest LIKE '%CBR 150%'
  AND interest_level = 'High'
  AND is_redundant = 0
ORDER BY predicted_next_purchase ASC;
```

---

## Sample Data Statistics

After running `populate_lead_data.py`:

- **360 Customers** with purchase histories
- **~250-300 Generated Leads** (customers with 2+ purchases)
- **Interest Level Distribution**:
  - High Interest: ~15-20%
  - Medium Interest: ~40-50%
  - Low Interest: ~30-40%

---

## Files Created

| File | Purpose |
|------|---------|
| `LeadDatabase.py` | Database class with business logic |
| `populate_lead_data.py` | Sample data generator (360 customers) |
| `lead_analysis.sqlite` | SQLite database file (created on first run) |
| `LEAD_ANALYSIS_README.md` | This documentation |

---

## Example SQL Queries

### Find upcoming high-interest leads
```sql
SELECT customer_name, product_interest, predicted_next_purchase,
       (julianday(predicted_next_purchase) - julianday('now')) as days_away
FROM LEADS
WHERE interest_level = 'High'
  AND is_redundant = 0
ORDER BY predicted_next_purchase ASC
LIMIT 20;
```

### Analyze buying patterns by product
```sql
SELECT product_purchased,
       COUNT(*) as total_customers,
       AVG(average_buying_cycle_days) as avg_cycle_days
FROM CUSTOMER_PROFILE_SALES
WHERE average_buying_cycle_days IS NOT NULL
GROUP BY product_purchased
ORDER BY total_customers DESC;
```

### Find customers with longest buying cycles
```sql
SELECT customer_name, product_purchased, average_buying_cycle_days
FROM CUSTOMER_PROFILE_SALES
WHERE average_buying_cycle_days IS NOT NULL
ORDER BY average_buying_cycle_days DESC
LIMIT 10;
```

---

## 🎯 Ready to Use!

Your Lead Analysis system is now complete with:
- ✅ Predictive lead generation
- ✅ Buying cycle calculation
- ✅ Redundancy checking
- ✅ 360 sample customers
- ✅ Integration with Agent system

Run `python populate_lead_data.py` to get started!
