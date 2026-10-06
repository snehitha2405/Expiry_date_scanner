import sqlite3
from datetime import date

DATABASE_NAME = "expiry_scanner.db"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ---------------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------------

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # Main inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            quantity INTEGER DEFAULT 1,
            batch_number TEXT,
            barcode TEXT,
            expiry_date TEXT,
            storage_location TEXT,
            status TEXT,
            image_path TEXT
        )
    """)

    # Barcode information learned from online/manual registration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barcode_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            product_name TEXT,
            brand TEXT,
            category TEXT
        )
    """)

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Add image_path if old database does not have it
    cursor.execute("PRAGMA table_info(products)")
    columns = [column["name"] for column in cursor.fetchall()]

    if "image_path" not in columns:
        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN image_path TEXT
        """)

    # Add default admin account
    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    )

    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    connection.commit()
    connection.close()


# ---------------------------------------------------------
# USER FUNCTIONS
# ---------------------------------------------------------

def create_user(username, password):
    username = username.strip()

    if not username:
        return False, "Username is required."

    if not password:
        return False, "Password is required."

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """,
            (username, password)
        )

        connection.commit()
        connection.close()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        connection.close()
        return False, "Username already exists."

    except Exception as error:
        connection.close()
        return False, str(error)


def verify_user(username, password):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        AND password = ?
        """,
        (username.strip(), password)
    )

    user = cursor.fetchone()

    connection.close()

    return user is not None


# ---------------------------------------------------------
# EXPIRY STATUS
# ---------------------------------------------------------

def calculate_status(expiry_date):
    if not expiry_date:
        return "Unknown"

    try:
        expiry = date.fromisoformat(str(expiry_date))
        today = date.today()

        days_left = (expiry - today).days

        if days_left < 0:
            return "Expired"

        elif days_left <= 3:
            return "Urgent"

        elif days_left <= 7:
            return "Attention"

        else:
            return "Safe"

    except Exception:
        return "Unknown"


# ---------------------------------------------------------
# BARCODE LOOKUP
# ---------------------------------------------------------

def get_product_by_barcode(barcode):
    if not barcode:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM barcode_products
        WHERE barcode = ?
        """,
        (str(barcode),)
    )

    product = cursor.fetchone()

    connection.close()

    return product


def save_barcode_product(
    barcode,
    product_name,
    brand="",
    category=""
):
    if not barcode:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO barcode_products
        (
            barcode,
            product_name,
            brand,
            category
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(barcode)
        DO UPDATE SET
            product_name = excluded.product_name,
            brand = excluded.brand,
            category = excluded.category
        """,
        (
            str(barcode),
            product_name,
            brand,
            category
        )
    )

    connection.commit()
    connection.close()

    return True


# ---------------------------------------------------------
# ADD PRODUCT
# ---------------------------------------------------------

def add_product(
    product_name,
    brand,
    category,
    quantity,
    batch_number,
    barcode,
    expiry_date,
    storage_location,
    image_path=""
):
    status = calculate_status(expiry_date)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO products
        (
            product_name,
            brand,
            category,
            quantity,
            batch_number,
            barcode,
            expiry_date,
            storage_location,
            status,
            image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_name,
            brand,
            category,
            quantity,
            batch_number,
            barcode,
            expiry_date,
            storage_location,
            status,
            image_path
        )
    )

    connection.commit()
    connection.close()

    return True


# ---------------------------------------------------------
# EXCEL / CSV IMPORT
# ---------------------------------------------------------

def add_product_from_excel(row):
    product_name = str(
        row.get("product_name", "")
    ).strip()

    brand = str(
        row.get("brand", "")
    ).strip()

    category = str(
        row.get("category", "")
    ).strip()

    batch_number = str(
        row.get("batch_number", "")
    ).strip()

    barcode = str(
        row.get("barcode", "")
    ).strip()

    expiry_date = str(
        row.get("expiry_date", "")
    ).strip()

    storage_location = str(
        row.get("storage_location", "")
    ).strip()

    try:
        quantity = int(
            row.get("quantity", 1)
        )
    except Exception:
        quantity = 1

    add_product(
        product_name=product_name,
        brand=brand,
        category=category,
        quantity=quantity,
        batch_number=batch_number,
        barcode=barcode,
        expiry_date=expiry_date,
        storage_location=storage_location
    )


# ---------------------------------------------------------
# UPDATE ALL PRODUCT STATUSES
# ---------------------------------------------------------

def update_all_statuses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, expiry_date FROM products"
    )

    products = cursor.fetchall()

    for product in products:
        status = calculate_status(
            product["expiry_date"]
        )

        cursor.execute(
            """
            UPDATE products
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                product["id"]
            )
        )

    connection.commit()
    connection.close()


# ---------------------------------------------------------
# GET ALL PRODUCTS
# ---------------------------------------------------------

def get_all_products():
    update_all_statuses()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        ORDER BY expiry_date ASC
        """
    )

    products = cursor.fetchall()

    connection.close()

    return products


# ---------------------------------------------------------
# STATUS COUNTS
# ---------------------------------------------------------

def get_status_counts():
    update_all_statuses()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM products
        GROUP BY status
        """
    )

    rows = cursor.fetchall()

    connection.close()

    counts = {
        "Safe": 0,
        "Attention": 0,
        "Urgent": 0,
        "Expired": 0,
        "Unknown": 0
    }

    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]

    return counts


# ---------------------------------------------------------
# SEARCH PRODUCTS
# ---------------------------------------------------------

def search_products(search_text):
    update_all_statuses()

    connection = get_connection()
    cursor = connection.cursor()

    search_text = f"%{search_text}%"

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE product_name LIKE ?
        OR brand LIKE ?
        OR category LIKE ?
        OR barcode LIKE ?
        OR batch_number LIKE ?
        ORDER BY expiry_date ASC
        """,
        (
            search_text,
            search_text,
            search_text,
            search_text,
            search_text
        )
    )

    products = cursor.fetchall()

    connection.close()

    return products


# ---------------------------------------------------------
# GET PRODUCTS BY STATUS
# ---------------------------------------------------------

def get_products_by_status(status):
    update_all_statuses()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE status = ?
        ORDER BY expiry_date ASC
        """,
        (status,)
    )

    products = cursor.fetchall()

    connection.close()

    return products


# ---------------------------------------------------------
# DELETE ONE PRODUCT
# ---------------------------------------------------------

def delete_product(product_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM products
        WHERE id = ?
        """,
        (product_id,)
    )

    connection.commit()
    connection.close()

    return True


# ---------------------------------------------------------
# DELETE ALL PRODUCTS
# ---------------------------------------------------------

def delete_all_products():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM products"
    )

    connection.commit()
    connection.close()

    return True


# ---------------------------------------------------------
# CREATE DATABASE
# ---------------------------------------------------------

create_tables()