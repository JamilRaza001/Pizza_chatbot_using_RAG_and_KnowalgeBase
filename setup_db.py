"""
Broadway Pizza - Database Setup Script (Expanded Knowledge Base)
=================================================================
This script initializes the SQLite database and seeds it with comprehensive
Broadway Pizza data including restaurant info, menu items, deals, and more.

Run this script once before starting the chatbot:
    python setup_db.py
"""

import sqlite3
import json
from pathlib import Path

# Import centralized configuration
from config import DB_PATH, VALID_TABLES, setup_logging

# Setup logging
logger = setup_logging(__name__)

# ============================================================================
# COMPREHENSIVE KNOWLEDGE BASE
# ============================================================================

KNOWLEDGE_BASE = {
    "restaurant": {
        "id": "rest_001",
        "name": "Broadway Pizza",
        "country": "Pakistan",
        "description": "A popular Pakistani pizza chain offering a wide variety of specialty pizzas, sides, wings, calzones, pastas, and deals.",
        "services": [
            "Dine-in",
            "Takeaway",
            "Home Delivery",
            "Online Ordering",
            "Catering",
            "Corporate Orders",
            "Birthday Orders",
             "Franchise Support"
        ],
        "payment_methods": [
            "Cash on Delivery",
            "Debit/Credit Card (Online)",
            "Mobile Wallets (Online)",
            "POS Machine (Selected branches)"
        ]
    },

    "menu_categories": [
        {"id": "cat_royale_pizza", "name": "Royale Flavors", "type": "pizza"},
        {"id": "cat_special_pizza", "name": "Specialty Pizzas", "type": "pizza"},
        {"id": "cat_king_crust", "name": "King Crust Pizzas", "type": "pizza"},
        {"id": "cat_starters", "name": "Appetizers & Starters", "type": "sides"},
        {"id": "cat_wings", "name": "Chicken Wings", "type": "sides"},
        {"id": "cat_calzones", "name": "Calzones", "type": "main"},
        {"id": "cat_pasta", "name": "Pastas", "type": "main"},
        {"id": "cat_kids", "name": "Kids Meals", "type": "kids"},
        {"id": "cat_desserts", "name": "Desserts", "type": "dessert"},
        {"id": "cat_beverages", "name": "Beverages & Sides", "type": "beverage"},
        {"id": "cat_deals", "name": "Deals", "type": "deal"}
    ],

    "menu_items": [
        # Royale Flavors (Pizzas)
        {
            "id": "item_mamamia",
            "category_id": "cat_royale_pizza",
            "category": "Royale Flavors",
            "name": "Mama Mia Classic",
            "description": "Smoked Chicken, Pepperoni, Veggies and Mozzarella over marinara sauce.",
            "sizes": "Small, Medium, Large, 20-Inch Slice",
            "base_price": 899
        },
        {
            "id": "item_wickedblend",
            "category_id": "cat_royale_pizza",
            "category": "Royale Flavors",
            "name": "Wicked Blend",
            "description": "Chicken Tikka, Fajita, Smoked Chicken with veggies and mozzarella.",
            "sizes": "Small, Medium, Large",
            "base_price": 949
        },
        {
            "id": "item_arabicranch",
            "category_id": "cat_royale_pizza",
            "category": "Royale Flavors",
            "name": "Arabic Ranch Pizza",
            "description": "Arabic kebab flavors with ranch sauce, veggies, and mozzarella.",
            "sizes": "Small, Medium, Large",
            "base_price": 999
        },
        {
            "id": "item_godspellbeef",
            "category_id": "cat_royale_pizza",
            "category": "Royale Flavors",
            "name": "Godspell Beef Load",
            "description": "Beef sausages, pepperoni, veggies and mozzarella.",
            "sizes": "Small, Medium, Large",
            "base_price": 1049
        },
        
        # Specialty Pizzas
        {
            "id": "item_wickedfajita",
            "category_id": "cat_special_pizza",
            "category": "Specialty Pizzas",
            "name": "Dancing Fajita Pizza",
            "description": "Chicken fajita, jalapenos, capsicum and mozzarella.",
            "sizes": "Small, Medium, Large",
            "base_price": 849
        },
        
        # King Crust Pizzas
        {
            "id": "item_kingchicken",
            "category_id": "cat_king_crust",
            "category": "King Crust Pizzas",
            "name": "King Crust Chicken",
            "description": "Stuffed crust pizza loaded with chicken, cheese, and kabab.",
            "sizes": "Large",
            "base_price": 1599
        },
        
        # Appetizers & Starters
        {
            "id": "item_gbread",
            "category_id": "cat_starters",
            "category": "Appetizers & Starters",
            "name": "Garlic Bread",
            "description": "Fresh bread with garlic butter topping.",
            "sizes": None,
            "base_price": 299
        },
        {
            "id": "item_megabites",
            "category_id": "cat_starters",
            "category": "Appetizers & Starters",
            "name": "Chicken Mega Bites",
            "description": "Crispy fried chicken bites.",
            "sizes": None,
            "base_price": 449
        },
        
        # Chicken Wings
        {
            "id": "item_plainwings",
            "category_id": "cat_wings",
            "category": "Chicken Wings",
            "name": "Plain Wings",
            "description": "Crispy & spicy chicken wings.",
            "sizes": None,
            "base_price": 549
        },
        {
            "id": "item_habanerowings",
            "category_id": "cat_wings",
            "category": "Chicken Wings",
            "name": "Habanero Wings",
            "description": "Wings coated with spicy habanero sauce.",
            "sizes": None,
            "base_price": 599
        },
        
        # Calzones
        {
            "id": "item_kebabzone",
            "category_id": "cat_calzones",
            "category": "Calzones",
            "name": "Kebab Zone Calzone",
            "description": "Chapli & Seekh kebab calzone with veggies.",
            "sizes": None,
            "base_price": 749
        },
        
        # Pastas
        {
            "id": "item_bbqpasta",
            "category_id": "cat_pasta",
            "category": "Pastas",
            "name": "BBQ Ranch Pasta",
            "description": "Chicken Tikka pasta with BBQ Ranch sauce.",
            "sizes": None,
            "base_price": 649
        },
        
        # Kids Meals
        {
            "id": "item_kiddymeal",
            "category_id": "cat_kids",
            "category": "Kids Meals",
            "name": "Kiddy Meal",
            "description": "Kids pizza meal with drink & puzzle.",
            "sizes": None,
            "base_price": 599
        },
        
        # Desserts
        {
            "id": "item_lavacake",
            "category_id": "cat_desserts",
            "category": "Desserts",
            "name": "Chocolate Lava Cake",
            "description": "Warm molten chocolate dessert.",
            "sizes": None,
            "base_price": 349
        },
        
        # Beverages
        {
            "id": "item_drinks",
            "category_id": "cat_beverages",
            "category": "Beverages & Sides",
            "name": "Soft Drinks",
            "description": "Chilled soft drinks in multiple flavors.",
            "sizes": "Small, Regular, Large",
            "base_price": 120
        }
    ],

    "deals": [
        {
            "id": "deal_mybox",
            "name": "My Box",
            "description": "Regular Pizza + Fries + Garlic Bread + Dip",
            "items_included": "Regular Pizza, Crinkle Fries, Garlic Bread (3 pcs), 1 Dip",
            "availability": "All Day",
            "base_price": 799
        },
        {
            "id": "deal_slice_box",
            "name": "Slice Box",
            "description": "20-Inch Slice + Fries + Garlic Bread + Dip",
            "items_included": "20 Inch Slice, Crinkle Fries, Garlic Bread, Dip",
            "availability": "All Day",
            "base_price": 649
        },
        {
            "id": "deal_crazy_double_small",
            "name": "Crazy Double - Small",
            "description": "2 Small Pizzas of your choice.",
            "items_included": "2 Small Pizzas",
            "availability": "All Day",
            "base_price": 1299
        },
        {
            "id": "deal_exclusive",
            "name": "Exclusive Deal",
            "description": "Medium Pizza + Lava Cake + Garlic Bread + 2 Dips",
            "items_included": "Medium Pizza, Lava Cake, Garlic Bread, 2 Dips",
            "availability": "All Day",
            "base_price": 1499
        },
        {
            "id": "deal_pepsi_strong",
            "name": "Pepsi Strong Deal",
            "description": "Medium Pizza + 2 Small Drinks",
            "items_included": "Medium Pizza, 2 Small Drinks",
            "availability": "All Day",
            "base_price": 1199
        }
    ],

    "dips": [
        {"id": "dip_garlic", "name": "Garlic Mayo", "price": 50},
        {"id": "dip_bbq", "name": "BBQ Ranch", "price": 50},
        {"id": "dip_jalapeno", "name": "Jalapeno Ranch", "price": 50},
        {"id": "dip_habanero", "name": "Habanero Sauce", "price": 50}
    ],

    "sizes": ["Small", "Medium", "Large", "20-Inch Slice"],

    "crust_types": [
        {"name": "Thin Crust", "extra_price": 0},
        {"name": "Deep Pan", "extra_price": 100},
        {"name": "Stuffed Crust (King Crust)", "extra_price": 200}
    ]
}


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the database schema for all tables."""
    cursor = conn.cursor()
    
    # Restaurant info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurant_info (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT,
            description TEXT,
            services TEXT,
            payment_methods TEXT
        )
    """)
    
    # Menu categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT
        )
    """)
    
    # Menu items table (expanded)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            category_id TEXT,
            description TEXT,
            sizes TEXT,
            price REAL DEFAULT 1000,
            FOREIGN KEY (category_id) REFERENCES menu_categories(id)
        )
    """)
    
    # Deals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            items_included TEXT,
            availability TEXT,
            price REAL DEFAULT 1000
        )
    """)
    
    # Dips table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dips (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL DEFAULT 50
        )
    """)
    
    # Crust types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crust_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            extra_price REAL DEFAULT 0
        )
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Chat Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chat Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    """)

    # Chat Summaries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_summaries (
            session_id TEXT PRIMARY KEY,
            summary TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    """)
    
    conn.commit()
    print("✅ All tables created successfully!")


def seed_data(conn: sqlite3.Connection) -> None:
    """Populate all tables with knowledge base data."""
    cursor = conn.cursor()
    
    # Clear existing data using whitelist-validated safe delete
    tables = ["restaurant_info", "menu_categories", "menu_items", "deals", "dips", "crust_types"]
    for table in tables:
        if table in VALID_TABLES:
            cursor.execute(f"DELETE FROM {table}")
            logger.debug(f"Cleared table: {table}")
        else:
            logger.warning(f"Skipped non-whitelisted table: {table}")
    
    # 1. Seed restaurant info
    rest = KNOWLEDGE_BASE["restaurant"]
    cursor.execute("""
        INSERT INTO restaurant_info (id, name, country, description, services, payment_methods)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        rest["id"], 
        rest["name"], 
        rest["country"], 
        rest["description"],
        json.dumps(rest["services"]),
        json.dumps(rest["payment_methods"])
    ))
    logger.info(f"Seeded restaurant info: {rest['name']}")
    
    # 2. Seed menu categories
    for cat in KNOWLEDGE_BASE["menu_categories"]:
        cursor.execute("""
            INSERT INTO menu_categories (id, name, type)
            VALUES (?, ?, ?)
        """, (cat["id"], cat["name"], cat["type"]))
    logger.info(f"Seeded {len(KNOWLEDGE_BASE['menu_categories'])} menu categories")
    
    # 3. Seed menu items
    for item in KNOWLEDGE_BASE["menu_items"]:
        cursor.execute("""
            INSERT INTO menu_items (id, name, category, category_id, description, sizes, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["id"],
            item["name"],
            item["category"],
            item["category_id"],
            item["description"],
            item.get("sizes"),
            item["base_price"]
        ))
    logger.info(f"Seeded {len(KNOWLEDGE_BASE['menu_items'])} menu items")
    
    # 4. Seed deals
    for deal in KNOWLEDGE_BASE["deals"]:
        cursor.execute("""
            INSERT INTO deals (id, name, description, items_included, availability, price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            deal["id"],
            deal["name"],
            deal["description"],
            deal["items_included"],
            deal["availability"],
            deal["base_price"]
        ))
    logger.info(f"Seeded {len(KNOWLEDGE_BASE['deals'])} deals")
    
    # 5. Seed dips
    for dip in KNOWLEDGE_BASE["dips"]:
        cursor.execute("""
            INSERT INTO dips (id, name, price)
            VALUES (?, ?, ?)
        """, (dip["id"], dip["name"], dip["price"]))
    logger.info(f"Seeded {len(KNOWLEDGE_BASE['dips'])} dips")
    
    # 6. Seed crust types
    for crust in KNOWLEDGE_BASE["crust_types"]:
        cursor.execute("""
            INSERT INTO crust_types (name, extra_price)
            VALUES (?, ?)
        """, (crust["name"], crust["extra_price"]))
    logger.info(f"Seeded {len(KNOWLEDGE_BASE['crust_types'])} crust types")
    
    conn.commit()


def verify_data(conn: sqlite3.Connection) -> None:
    """Display the seeded data for verification."""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📋 DATABASE VERIFICATION")
    print("=" * 60)
    
    # Restaurant info
    cursor.execute("SELECT name, country FROM restaurant_info")
    rest = cursor.fetchone()
    if rest:
        print(f"\n🏪 Restaurant: {rest[0]} ({rest[1]})")
    
    # Categories
    cursor.execute("SELECT COUNT(*) FROM menu_categories")
    cat_count = cursor.fetchone()[0]
    print(f"📁 Categories: {cat_count}")
    
    # Menu items by category
    print("\n🍕 Menu Items by Category:")
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM menu_items 
        GROUP BY category
    """)
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} items")
    
    # Deals
    cursor.execute("SELECT COUNT(*) FROM deals")
    deal_count = cursor.fetchone()[0]
    print(f"\n🎁 Deals: {deal_count}")
    
    # Dips
    cursor.execute("SELECT COUNT(*) FROM dips")
    dip_count = cursor.fetchone()[0]
    print(f"🥣 Dips: {dip_count}")
    
    # Crust types
    cursor.execute("SELECT COUNT(*) FROM crust_types")
    crust_count = cursor.fetchone()[0]
    print(f"🍞 Crust Types: {crust_count}")
    
    print("\n" + "=" * 60)


def initialize_database() -> None:
    """Main function to initialize and seed the database."""
    print("🍕 Broadway Pizza - Expanded Knowledge Base Setup")
    print("=" * 50)
    
    # Create connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Create tables
        create_tables(conn)
        
        # Seed all data
        seed_data(conn)
        
        # Verify data
        verify_data(conn)
        
        print(f"\n✅ Database initialized at: {DB_PATH}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
