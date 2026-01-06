"""
Broadway Pizza Customer Chatbot (Persistent Memory Version)
===========================================================
A customer-facing AI chatbot for Broadway Pizza Pakistan.
Features persistent context memory, summarization, and RAG.

Run: streamlit run app.py
"""

import os
import json
import re
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Optional, Tuple, List

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Import local modules
from config import (
    DB_PATH, SIZE_MULTIPLIERS, setup_logging,
    LLM_MODEL_NAME, LLM_MAX_RETRIES, LLM_BASE_DELAY,
    MEMORY_SUMMARY_THRESHOLD
)
from database import DatabaseConnection, DatabaseError
from models import CustomerInfo, CartItem, Cart
from memory import ChatMemory
import setup_db

# Try to import fuzzy matching
try:
    from thefuzz import fuzz, process
    FUZZY_ENABLED = True
except ImportError:
    FUZZY_ENABLED = False

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging(__name__)

# Initialize database
if not DB_PATH.exists():
    with st.spinner("Initializing Knowledge Base..."):
        setup_db.initialize_database()
        logger.info("Database initialized")


# =============================================================================
# RETRY DECORATOR FOR API CALLS (Fix #4)
# =============================================================================

def retry_with_backoff(max_retries: int = LLM_MAX_RETRIES, base_delay: float = LLM_BASE_DELAY):
    """Decorator for exponential backoff retry on API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator


@retry_with_backoff()
def call_gemini_with_retry(chat, prompt: str) -> str:
    """Call Gemini API with retry logic and null check."""
    response = chat.send_message(prompt)
    if response.text is None:
        raise ValueError("Empty response from Gemini API")
    return response.text


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def init_session():
    """Initialize session ID using query parameters for persistence."""
    query_params = st.query_params
    session_id = query_params.get("session_id", None)
    
    if not session_id:
        session_id = str(uuid.uuid4())
        st.query_params["session_id"] = session_id
        logger.info(f"Created new session: {session_id}")
    
    return session_id

# Initialize persistent memory
SESSION_ID = init_session()
memory = ChatMemory(session_id=SESSION_ID)


# =============================================================================
# RAG FUNCTIONS
# =============================================================================

def get_restaurant_info() -> str:
    """Get information about Broadway Pizza restaurant."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, country, description, services, payment_methods FROM restaurant_info")
            row = cursor.fetchone()
        
        if not row: return "Restaurant information not available."
        
        name, country, description, services_json, payments_json = row
        services = json.loads(services_json)
        payments = json.loads(payments_json)
        
        info = f"🍕 **{name}** ({country})\n\n{description}\n\n**🛎️ Services We Offer:**\n"
        for service in services: info += f"• {service}\n"
        info += "\n**💳 Payment Methods:**\n"
        for payment in payments: info += f"• {payment}\n"
        
        return info
    except DatabaseError as e:
        logger.error(f"Error getting restaurant info: {e}")
        return "Error getting restaurant info."

def query_menu_db(query: Optional[str] = None) -> str:
    """Query the Broadway Pizza menu from the database with flexible search."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            if query:
                search_term = f"%{query}%"
                cursor.execute(
                    """SELECT name, category, description, sizes, price 
                       FROM menu_items 
                       WHERE name LIKE ? OR category LIKE ? OR description LIKE ?""",
                    (search_term, search_term, search_term)
                )
            else:
                cursor.execute("SELECT name, category, description, sizes, price FROM menu_items")
            
            rows = cursor.fetchall()
            
            if query and any(q in query.lower() for q in ['deal', 'offer']):
                cursor.execute("SELECT name, 'Deals', description, items_included, price FROM deals")
                deal_rows = cursor.fetchall()
                for d in deal_rows:
                    rows.append((d[0], d[1], d[2] + f" ({d[3]})", "Standard", d[4]))
        
        if not rows: return ""
        
        menu_text = f"🔎 **Found results for '{query}':**\n\n" if query else "🍕 **Broadway Pizza Menu**\n\n"
        categories = {}
        for name, cat, desc, sizes, price in rows:
            if cat not in categories: categories[cat] = []
            size_info = f" | Sizes: {sizes}" if sizes and sizes != "Standard" else ""
            categories[cat].append(f"• **{name}** - Rs. {int(price)}{size_info}\n  _{desc}_")
        
        for cat, items in categories.items():
            menu_text += f"**📂 {cat}:**\n" + "\n".join(items) + "\n\n"
        return menu_text
    except DatabaseError as e:
        logger.error(f"Error querying menu: {e}")
        return "Error querying menu."

def get_deals() -> str:
    """Get all available deals."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, description, items_included, availability, price FROM deals")
            rows = cursor.fetchall()
        
        if not rows: return "No deals available."
        
        deals_text = "🎁 **Broadway Pizza Deals**\n\n"
        for name, desc, items, availability, price in rows:
            deals_text += f"**🔥 {name}** - Rs. {int(price)}\n_{desc}_\n📦 Includes: {items}\n⏰ Available: {availability}\n\n"
        return deals_text
    except DatabaseError as e:
        logger.error(f"Error getting deals: {e}")
        return "Error getting deals."

def get_dips_and_extras() -> str:
    """Get available dips and crust types."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, price FROM dips")
            dips = cursor.fetchall()
            cursor.execute("SELECT name, extra_price FROM crust_types")
            crusts = cursor.fetchall()
        
        result = "🥣 **Dips & Sauces:**\n"
        for name, price in dips: result += f"• {name} - Rs. {int(price)}\n"
        result += "\n🍞 **Crust Options:**\n"
        for name, extra_price in crusts:
            result += f"• {name} (+Rs. {int(extra_price)})\n" if extra_price > 0 else f"• {name} (Standard)\n"
        return result
    except DatabaseError as e:
        logger.error(f"Error getting extras: {e}")
        return "Error getting extras."

def get_menu_categories() -> str:
    """Get all menu categories."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, type FROM menu_categories")
            rows = cursor.fetchall()
        
        if not rows: return "No categories found."
        
        result = "📂 **Menu Categories:**\n\n"
        for name, cat_type in rows:
            emoji = {"pizza": "🍕", "sides": "🍟", "main": "🍝", "kids": "👶", "dessert": "🍰", "beverage": "🥤", "deal": "🎁"}.get(cat_type, "•")
            result += f"{emoji} {name}\n"
        result += "\nAsk me about any category to see items!"
        return result
    except DatabaseError as e:
        logger.error(f"Error getting categories: {e}")
        return "Error getting categories."

def get_all_menu_items() -> List[Tuple]:
    """Get all items for fuzzy matching."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            all_items = []
            cursor.execute("SELECT name, category, sizes, price FROM menu_items")
            for row in cursor.fetchall(): all_items.append(tuple(row))
            cursor.execute("SELECT name, 'Deals', NULL, price FROM deals")
            for row in cursor.fetchall(): all_items.append(tuple(row))
        return all_items
    except DatabaseError: return []

def find_menu_item(user_message: str) -> Optional[Tuple]:
    """Find a menu item using fuzzy matching."""
    all_items = get_all_menu_items()
    if not all_items: return None
    
    message_lower = user_message.lower()
    # Exact match first
    for item in sorted(all_items, key=lambda x: len(x[0]), reverse=True):
        if item[0].lower() in message_lower: return item
    
    # Fuzzy match
    if FUZZY_ENABLED:
        item_names = [item[0] for item in all_items]
        words = message_lower.split()
        for phrase_len in range(min(5, len(words)), 0, -1):
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len])
                if len(phrase) > 3:
                    match = process.extractOne(phrase, item_names, scorer=fuzz.ratio)
                    if match and match[1] >= 70:
                        matched_name = match[0]
                        for item in all_items:
                            if item[0] == matched_name: return item
    return None

def save_order_to_db(customer: CustomerInfo, cart: Cart) -> str:
    """Save order to DB."""
    if cart.is_empty(): return "❌ Your cart is empty."
    try:
        items_json = json.dumps(cart.to_order_json())
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (customer_name, customer_phone, items_json, total_amount)
                VALUES (?, ?, ?, ?)
            """, (customer.name, customer.phone, items_json, cart.total_price))
            order_id = cursor.lastrowid
            conn.commit()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confirmation = f"""
✅ **Order Confirmed!**
📋 **Order ID:** #{order_id}
👤 **Name:** {customer.name}
📱 **Phone:** {customer.masked_phone()}
⏰ **Time:** {timestamp}

**📦 Items Ordered:**
"""
        for item in cart.items:
            confirmation += f"• {item.display_name()} x{item.quantity} - Rs. {int(item.total_price)}\n"
        
        confirmation += f"""
💰 **Total Amount:** Rs. {int(cart.total_price)}
📌 **Status:** Pending
"""
        return confirmation
    except DatabaseError as e:
        logger.error(f"Error placing order: {e}")
        return "❌ Error placing order."

def detect_intent_and_get_context(user_message: str) -> str:
    """Detect intent and fetch RAG context with batched queries (Fix #8)."""
    message_lower = user_message.lower()
    context_parts = []
    
    # Batch keyword search into single query instead of N queries
    stop_words = {"i", "want", "a", "the", "please", "can", "you", "give", "me", "show", "is", "of"}
    keywords = [word for word in message_lower.split() if word not in stop_words and len(word) > 2]
    
    if keywords:
        # Single batched query for all keywords
        results = query_menu_db_batch(keywords)
        if results:
            context_parts.append(results)
    
    # Intent-based additions
    if "menu" in message_lower or "food" in message_lower:
        context_parts.append(query_menu_db())
    if any(w in message_lower for w in ["deal", "offer"]):
        context_parts.append(get_deals())
    if any(w in message_lower for w in ["dip", "sauce", "extra"]):
        context_parts.append(get_dips_and_extras())
    if any(w in message_lower for w in ["service", "payment", "info"]):
        context_parts.append(get_restaurant_info())
    if "categor" in message_lower:
        context_parts.append(get_menu_categories())
    
    return "\n".join(filter(None, context_parts))


def query_menu_db_batch(keywords: list) -> str:
    """Query menu with multiple keywords in single query (Fix #8)."""
    if not keywords:
        return ""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            # Build OR conditions for all keywords in single query
            conditions = " OR ".join(
                "(name LIKE ? OR category LIKE ? OR description LIKE ?)" 
                for _ in keywords
            )
            params = []
            for kw in keywords:
                term = f"%{kw}%"
                params.extend([term, term, term])
            
            cursor.execute(f"""
                SELECT DISTINCT name, category, description, sizes, price 
                FROM menu_items 
                WHERE {conditions}
            """, params)
            rows = cursor.fetchall()
        
        if not rows:
            return ""
        
        menu_text = "🔎 **Search Results:**\n\n"
        categories = {}
        for name, cat, desc, sizes, price in rows:
            if cat not in categories:
                categories[cat] = []
            size_info = f" | Sizes: {sizes}" if sizes and sizes != "Standard" else ""
            categories[cat].append(f"• **{name}** - Rs. {int(price)}{size_info}\n  _{desc}_")
        
        for cat, items in categories.items():
            menu_text += f"**📂 {cat}:**\n" + "\n".join(items) + "\n\n"
        return menu_text
    except DatabaseError as e:
        logger.error(f"Error in batch query: {e}")
        return ""

def format_cart_for_display(cart: Cart) -> str:
    if cart.is_empty(): return "🛒 Your cart is empty."
    cart_text = "🛒 **Your Cart:**\n\n"
    for i, item in enumerate(cart.items, 1):
        cart_text += f"{i}. {item.display_name()} x{item.quantity} - Rs. {int(item.total_price)}\n"
    cart_text += f"\n**💰 Total: Rs. {int(cart.total_price)}**"
    return cart_text

def parse_size_from_message(message: str) -> Optional[str]:
    message_lower = message.lower()
    size_keywords = {
        "small": "Small", "medium": "Medium", "large": "Large",
        "slice": "20-Inch Slice", "20-inch": "20-Inch Slice", "regular": "Small"
    }
    for keyword, size in size_keywords.items():
        if keyword in message_lower: return size
    return None

def process_cart_commands(user_message: str, cart: Cart) -> Tuple[Cart, Optional[str]]:
    message_lower = user_message.lower()
    
    # Remove
    if match := re.search(r'remove\s+(?:item\s+)?#?(\d+)', message_lower):
        removed = cart.remove_item(int(match.group(1)))
        return cart, f"✅ Removed **{removed.display_name()}**." if removed else "❌ Invalid item number."
    
    # Update
    if match := re.search(r'update\s+#?(\d+)\s+quantity\s+(\d+)', message_lower):
        updated = cart.update_quantity(int(match.group(1)), int(match.group(2)))
        return cart, "✅ Quantity updated." if updated else "❌ Update failed."
    
    # Add
    if any(k in message_lower for k in ["add", "want", "order", "have"]):
        item = find_menu_item(user_message)
        if item:
            name, category, sizes, price = item
            size = parse_size_from_message(user_message) if sizes else None
            cart_item = CartItem(
                name=name, category=category, base_price=float(price),
                quantity=1, size=size,
                size_multiplier=SIZE_MULTIPLIERS.get(size, 1.0) if size else 1.0
            )
            cart.add_item(cart_item)
            return cart, f"✅ Added **{name}** to cart."
            
    # View/Clear
    if "view cart" in message_lower: return cart, format_cart_for_display(cart)
    if "clear cart" in message_lower: 
        cart.clear()
        return cart, "🗑️ Cart cleared."
        
    return cart, None

def extract_customer_info(message: str) -> Tuple[Optional[str], Optional[str]]:
    phone_match = re.search(r'(\+?92|0)?[-\s]?3\d{2}[-\s]?\d{7}', message)
    phone = phone_match.group(0) if phone_match else None
    
    name_match = re.search(r"(?:my name is|i'm|name:?\s*)([A-Za-z]+(?:\s+[A-Za-z]+)?)", message, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else None
    
    return name, phone


# =============================================================================
# CART SERIALIZATION HELPERS (Fix #7)
# =============================================================================

def save_cart_to_session(cart: Cart):
    """Serialize cart to session state safely."""
    st.session_state.cart_data = cart.model_dump()

def load_cart_from_session() -> Cart:
    """Deserialize cart from session state."""
    if "cart_data" in st.session_state:
        return Cart.model_validate(st.session_state.cart_data)
    return Cart()


# =============================================================================
# MAIN APP
# =============================================================================

def get_gemini_model(history=None):
    """Initialize Gemini with history context using centralized config."""
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key: st.error("Missing Google API Key."); st.stop()
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=LLM_MODEL_NAME,  # Fix #3: Use centralized config
        system_instruction="""You are a friendly waiter for Broadway Pizza Pakistan.
Role: Help browse menu, take orders, answer questions.
Context: You have access to a summary of the previous conversation and specific menu details.
Goals: Be helpful, accurate with prices/menu, suggest deals.
"""
    )
    return model.start_chat(history=history or [])

def main():
    st.set_page_config(page_title="Broadway Pizza Chatbot", page_icon="🍕")
    st.title("🍕 Broadway Pizza")
    
    if st.query_params.get("debug"):
        st.caption(f"Session ID: {SESSION_ID}")

    # Initialize Cart using serialization helpers (Fix #7)
    cart = load_cart_from_session()
    if "awaiting_info" not in st.session_state: st.session_state.awaiting_info = False

    # Load & Display History
    full_history = memory.get_all_history()
    if not full_history:
        welcome = "👋 Welcome to Broadway Pizza! I remember you. Check out our menu or deals!"
        memory.save_message("assistant", welcome)
        full_history = [{"role": "assistant", "content": welcome}]

    for msg in full_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Order here..."):
        with st.chat_message("user"): st.markdown(prompt)
        memory.save_message("user", prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response_text = ""
                    if st.session_state.awaiting_info and not cart.is_empty():
                        name, phone = extract_customer_info(prompt)
                        if name and phone:
                            # 1. LINK USER IDENTITY (Primary Key Logic)
                            memory.associate_user(phone)
                            
                            try:
                                customer = CustomerInfo(name=name, phone=phone)
                                response_text = save_order_to_db(customer, cart)
                                cart = Cart()  # Reset cart
                                st.session_state.awaiting_info = False
                            except ValueError as e: response_text = f"⚠️ {e}"
                        else: response_text = "Please provide Name and Phone to confirm."
                    else:
                        cart, cart_msg = process_cart_commands(prompt, cart)
                        if cart_msg: response_text = cart_msg
                        elif "checkout" in prompt.lower():
                             if not cart.is_empty():
                                st.session_state.awaiting_info = True
                                response_text = format_cart_for_display(cart) + "\n\nPlease provide Name and Phone."
                             else: response_text = "Cart is empty."
                        else:
                            rag_context = detect_intent_and_get_context(prompt)
                            cart_context = format_cart_for_display(cart)
                            history_window = memory.build_context_window()
                            
                            full_prompt = f"""CONTEXT:\n{rag_context}\n\nCART:\n{cart_context}\n\nUSER MESSAGE:\n{prompt}"""
                            
                            chat = get_gemini_model(history=history_window)
                            # Fix #4: Use retry helper for LLM call
                            response_text = call_gemini_with_retry(chat, full_prompt)
                    
                    st.markdown(response_text)
                    memory.save_message("assistant", response_text)
                    
                    # Save cart state (Fix #7)
                    save_cart_to_session(cart)
                    
                    # Only summarize when threshold is crossed (Fix #2)
                    # Note: generate_summary internally checks the threshold now
                    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
                    memory.generate_summary(api_key)
                    
                except Exception as e:
                    logger.error(f"Error: {e}")
                    st.error("I'm having trouble connecting right now.")

if __name__ == "__main__":
    main()
