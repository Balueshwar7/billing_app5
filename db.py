# db.py
import mysql.connector
from datetime import datetime

# 1. Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="998967",
        database="food_truck"
    )

# 2. Save a bill and its items to the database
def save_bill_to_db(bill_items, total):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM bills")
        customer_number = cursor.fetchone()[0] + 1

        now = datetime.now()
        cursor.execute("""
            INSERT INTO bills (customer_number, date_time, total)
            VALUES (%s, %s, %s)
        """, (customer_number, now, total))

        bill_id = cursor.lastrowid

        for item in bill_items:
            cursor.execute("""
                INSERT INTO bill_items (bill_id, item_name, quantity, price, total)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                bill_id,
                item['name'],
                item['qty'],
                item['price'],
                item['qty'] * item['price']
            ))

        conn.commit()
        print("✅ Bill saved to database.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving to DB: {e}")
    finally:
        cursor.close()
        conn.close()

# 3. Load menu items from the database
def get_menu_items():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT name, price FROM menu_items")
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error loading menu items: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# 4. Save a new menu item to the database
def add_menu_item_to_db(name, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO menu_items (name, price)
            VALUES (%s, %s)
        """, (name, price))
        conn.commit()
        print(f"✅ Menu item '{name}' added to database.")
    except mysql.connector.IntegrityError:
        print(f"⚠️ Menu item '{name}' already exists. Skipping.")
    except Exception as e:
        print(f"❌ Error adding menu item: {e}")
    finally:
        cursor.close()
        conn.close()

# 5. Delete a menu item from the database
def delete_menu_item_from_db(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM menu_items WHERE name = %s", (name,))
        conn.commit()
    except Exception as e:
        print(f"❌ Error deleting item: {e}")
    finally:
        cursor.close()
        conn.close()

# 6. Load all bills with items for admin panel
def get_all_bills():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.id, b.customer_number, b.date_time, b.total,
                   GROUP_CONCAT(CONCAT(bi.item_name, ' x', bi.quantity) SEPARATOR ', ') as items
            FROM bills b
            LEFT JOIN bill_items bi ON b.id = bi.bill_id
            GROUP BY b.id
            ORDER BY b.date_time DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error loading bills: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
