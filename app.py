"""
Broadway Pizza Customer Chatbot (Expanded Knowledge Base)
==========================================================
A customer-facing AI chatbot for Broadway Pizza Pakistan.
Uses Streamlit for the chat interface and Google Gemini for AI.

Features:
- Comprehensive menu browsing via RAG (queries real SQLite database)
- Restaurant info, deals, dips, crust types knowledge
- Cart management with session state
- Order placement with database storage

Run: streamlit run app.py
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import setup_db  # Import the setup script

# Load environment variables from .env file
load_dotenv()


# Database path
DB_PATH = Path(__file__).parent / "broadway_pizza.db"

# Initialize database if it doesn't exist (Critical for Streamlit Cloud)
if not DB_PATH.exists():
    with st.spinner("Initializing Knowledge Base..."):
        setup_db.initialize_database()


# =============================================================================
# RAG FUNCTIONS - These enable fetching real data from SQLite database
# =============================================================================
# 
# CRUCIAL: The RAG (Retrieval-Augmented Generation) architecture works by:
# 1. User asks a question like "Show me the menu" or "What deals do you have?"
# 2. We detect keywords and call appropriate database query function
# 3. The function returns actual data from the database
# 4. This data is passed to Gemini as context for accurate responses
#
# This ensures the chatbot provides accurate, up-to-date information
# rather than hallucinating or using outdated training data.
# =============================================================================

def get_restaurant_info() -> str:
    """Get information about Broadway Pizza restaurant."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, country, description, services, payment_methods FROM restaurant_info")
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return "Restaurant information not available."
        
        name, country, description, services_json, payments_json = row
        services = json.loads(services_json)
        payments = json.loads(payments_json)
        
        info = f"""🍕 **{name}** ({country})

{description}

**🛎️ Services We Offer:**
"""
        for service in services:
            info += f"• {service}\n"
        
        info += "\n**💳 Payment Methods:**\n"
        for payment in payments:
            info += f"• {payment}\n"
        
        return info
        
    except Exception as e:
        return f"Error getting restaurant info: {str(e)}"


def query_menu_db(query: Optional[str] = None) -> str:
    """Query the Broadway Pizza menu from the database with flexible search."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if query:
            # Search in name, category, or description
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
        
        # Also check deals if keyword matches
        if query and any(q in query.lower() for q in ['deal', 'offer']):
            cursor.execute("SELECT name, 'Deals', description, items_included, price FROM deals")
            deal_rows = cursor.fetchall()
            # Adapt structure for deals to match menu items
            for d in deal_rows:
                rows.append((d[0], d[1], d[2] + f" ({d[3]})", "Standard", d[4]))

        conn.close()
        
        if not rows:
            return ""
        
        menu_text = ""
        if query:
            menu_text += f"🔎 **Found results for '{query}':**\n\n"
        else:
            menu_text += "🍕 **Broadway Pizza Menu**\n\n"
        
        categories = {}
        for name, cat, desc, sizes, price in rows:
            if cat not in categories:
                categories[cat] = []
            
            size_info = f" | Sizes: {sizes}" if sizes and sizes != "Standard" else ""
            categories[cat].append(f"• **{name}** - Rs. {int(price)}{size_info}\n  _{desc}_")
        
        for cat, items in categories.items():
            menu_text += f"**📂 {cat}:**\n"
            menu_text += "\n".join(items)
            menu_text += "\n\n"
        
        return menu_text
        
    except Exception as e:
        return f"Error querying menu: {str(e)}"


def get_deals() -> str:
    """Get all available deals from Broadway Pizza."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, description, items_included, availability, price FROM deals")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No deals available at the moment."
        
        deals_text = "🎁 **Broadway Pizza Deals**\n\n"
        
        for name, desc, items, availability, price in rows:
            deals_text += f"**🔥 {name}** - Rs. {int(price)}\n"
            deals_text += f"_{desc}_\n"
            deals_text += f"📦 Includes: {items}\n"
            deals_text += f"⏰ Available: {availability}\n\n"
        
        return deals_text
        
    except Exception as e:
        return f"Error getting deals: {str(e)}"


def get_dips_and_extras() -> str:
    """Get available dips and crust types."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, price FROM dips")
        dips = cursor.fetchall()
        
        cursor.execute("SELECT name, extra_price FROM crust_types")
        crusts = cursor.fetchall()
        
        conn.close()
        
        result = "🥣 **Dips & Sauces:**\n"
        for name, price in dips:
            result += f"• {name} - Rs. {int(price)}\n"
        
        result += "\n🍞 **Crust Options:**\n"
        for name, extra_price in crusts:
            if extra_price > 0:
                result += f"• {name} (+Rs. {int(extra_price)})\n"
            else:
                result += f"• {name} (Standard)\n"
        
        return result
        
    except Exception as e:
        return f"Error getting extras: {str(e)}"


def get_menu_categories() -> str:
    """Get all menu categories available."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, type FROM menu_categories")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No categories found."
        
        result = "📂 **Menu Categories:**\n\n"
        
        for name, cat_type in rows:
            emoji = {
                "pizza": "🍕",
                "sides": "🍟",
                "main": "🍝",
                "kids": "👶",
                "dessert": "🍰",
                "beverage": "🥤",
                "deal": "🎁"
            }.get(cat_type, "•")
            result += f"{emoji} {name}\n"
        
        result += "\nAsk me about any category to see items!"
        return result
        
    except Exception as e:
        return f"Error getting categories: {str(e)}"


def find_menu_item(item_name: str):
    """Find a menu item or deal by name."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First check menu_items
        cursor.execute(
            "SELECT name, category, sizes, price FROM menu_items WHERE name LIKE ?",
            (f"%{item_name}%",)
        )
        row = cursor.fetchone()
        
        # If not found in menu_items, check deals
        if not row:
            cursor.execute(
                "SELECT name, 'Deals' as category, NULL as sizes, price FROM deals WHERE name LIKE ?",
                (f"%{item_name}%",)
            )
            row = cursor.fetchone()
        
        conn.close()
        return row
        
    except Exception:
        return None


def save_order_to_db(customer_name: str, customer_phone: str, cart: list) -> str:
    """Save the confirmed order to the database."""
    if not cart:
        return "❌ Cannot place order - your cart is empty. Please add items first."
    
    try:
        total = sum(item["price"] * item["quantity"] for item in cart)
        items_json = json.dumps(cart)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO orders (customer_name, customer_phone, items_json, total_amount)
            VALUES (?, ?, ?, ?)
        """, (customer_name, customer_phone, items_json, total))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        confirmation = f"""
✅ **Order Confirmed!**

📋 **Order ID:** #{order_id}
👤 **Name:** {customer_name}
📱 **Phone:** {customer_phone}
⏰ **Time:** {timestamp}

**📦 Items Ordered:**
"""
        for item in cart:
            size_info = f" ({item['size']})" if item.get('size') else ""
            confirmation += f"• {item['name']}{size_info} x{item['quantity']} - Rs. {item['price'] * item['quantity']}\n"
        
        confirmation += f"""
💰 **Total Amount:** Rs. {total}
📌 **Status:** Pending

🍕 Thank you for ordering from Broadway Pizza Pakistan!
Your delicious order will be prepared shortly.

**Payment:** Cash on Delivery / Card at doorstep
"""
        return confirmation
        
    except Exception as e:
        return f"❌ Error placing order: {str(e)}"


# =============================================================================
# INTENT DETECTION & CONTEXT BUILDING
# =============================================================================

def detect_intent_and_get_context(user_message: str) -> str:
    """
    Detect user intent and fetch relevant data from database.
    This now uses a broader search strategy to ensure relevant content is found.
    """
    message_lower = user_message.lower()
    context = ""
    
    # 1. ALWAYS Try to find relevant menu items based on keywords in the message
    # Filter out common stop words to avoid fetching everything for "I want a..."
    stop_words = ["i", "want", "a", "the", "please", "can", "you", "give", "me", "show", "is", "of", "do", "have"]
    keywords = [word for word in message_lower.split() if word not in stop_words and len(word) > 2]
    
    if keywords:
        # Search for the most relevant keyword (simplistic but effective for now)
        # In a real app, we'd search for all or use vector search
        for keyword in keywords:
            results = query_menu_db(keyword)
            if results and results not in context:
                context += results + "\n"
    
    # 2. Check for broad categories if specific items weren't enough
    if "menu" in message_lower or "food" in message_lower:
        context += query_menu_db() + "\n"
    
    # 3. Check for specific high-level intents
    if any(word in message_lower for word in ["deal", "offer", "combo"]):
        context += get_deals() + "\n"
    
    if any(word in message_lower for word in ["dip", "sauce", "crust", "extra"]):
        context += get_dips_and_extras() + "\n"
        
    if any(word in message_lower for word in ["service", "delivery", "payment", "pay", "about", "info", "location", "contact"]):
        context += get_restaurant_info() + "\n"
        
    if any(word in message_lower for word in ["categor", "types", "kinds"]):
        context += get_menu_categories() + "\n"
        
    return context


# =============================================================================
# CHATBOT SETUP
# =============================================================================

def get_gemini_model():
    """Initialize and return the Gemini model."""
    # Try getting API key from Streamlit secrets (for Cloud) or .env (local)
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        st.error("❌ GOOGLE_API_KEY not found. Please set it in .env (local) or Streamlit Secrets (cloud).")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction="""You are a friendly and efficient waiter for Broadway Pizza Pakistan - a popular pizza chain known for delicious specialty pizzas, sides, and amazing deals!

**Your Role:**
- Help customers browse the menu
- Take orders and manage their cart
- Answer questions about food, services, and payment methods
- Guide customers through the ordering process

**Order Flow:**
1. Greet and help browse menu/deals
2. When customer wants to order, confirm the item and add to cart
3. Ask if they want more items or proceed to checkout
4. For checkout, ask for Name and Phone Number
5. Confirm the order

**Guidelines:**
- Be friendly, helpful, and use emojis 🍕
- Use the menu/deals data provided in the context to give accurate information
- Never make up menu items or prices - only use data from the context
- Suggest deals and combos proactively
- Confirm order details before finalizing
- Mention payment options (Cash on Delivery, Card)

**Cart Commands (for you to understand):**
- When user says "add [item]" or "I want [item]", respond with confirmation and ask about quantity/size
- When user says "checkout" or "place order", ask for their name and phone
- When user provides name and phone, confirm the order

Always be warm and welcoming!"""
    )
    
    return model


def format_cart_for_display(cart: list) -> str:
    """Format cart for display."""
    if not cart:
        return "🛒 Your cart is empty."
    
    cart_text = "🛒 **Your Cart:**\n\n"
    total = 0
    
    for i, item in enumerate(cart, 1):
        item_total = item["price"] * item["quantity"]
        size_info = f" ({item['size']})" if item.get('size') else ""
        cart_text += f"{i}. {item['name']}{size_info} x{item['quantity']} - Rs. {item_total}\n"
        total += item_total
    
    cart_text += f"\n**💰 Total: Rs. {total}**"
    return cart_text


def process_order_intent(user_message: str, cart: list) -> tuple:
    """Process ordering intents and return updated cart and response."""
    message_lower = user_message.lower()
    response = None
    
    # Check for add to cart intent
    add_keywords = ["add", "want", "order", "give me", "i'll have", "get me", "please add"]
    if any(keyword in message_lower for keyword in add_keywords):
        # Try to find the item
        item = find_menu_item(user_message)
        if item:
            name, category, sizes, price = item
            
            cart.append({
                "name": name,
                "category": category,
                "price": price,
                "quantity": 1,
                "size": None
            })
            
            total = sum(i["price"] * i["quantity"] for i in cart)
            response = f"""✅ Added to cart:
• 1x **{name}** - Rs. {price}

🛒 **Cart:** {len(cart)} item(s) | **Total: Rs. {total}**

Would you like to:
• Add more items?
• See the menu or deals?
• Proceed to checkout?"""
    
    # Check for view cart
    if any(word in message_lower for word in ["cart", "my order", "what did i order", "show order"]):
        response = format_cart_for_display(cart)
        if cart:
            response += "\n\nTo confirm your order, please provide your **Name** and **Phone Number**."
    
    # Check for clear cart
    if any(word in message_lower for word in ["clear cart", "remove all", "start over", "cancel order"]):
        cart.clear()
        response = "🗑️ Your cart has been cleared. Would you like to start a new order?"
    
    return cart, response


def extract_customer_info(message: str) -> tuple:
    """Try to extract name and phone from message."""
    import re
    
    # Common patterns for phone numbers in Pakistan
    phone_pattern = r'(\+?92|0)?[-\s]?3\d{2}[-\s]?\d{7}'
    phone_match = re.search(phone_pattern, message)
    phone = phone_match.group(0) if phone_match else None
    
    # Simple name extraction (after "name is" or "I'm" or "I am")
    name_patterns = [
        r"(?:my name is|i'm|i am|name:?)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        r"^([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:and|,)",
    ]
    
    name = None
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            break
    
    return name, phone


# =============================================================================
# STREAMLIT UI
# =============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Broadway Pizza Chatbot",
        page_icon="🍕",
        layout="centered"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #e63946;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🍕 Broadway Pizza")
    st.caption("Pakistan's Favorite Pizza | AI-Powered Ordering Assistant")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    if "chat_session" not in st.session_state:
        model = get_gemini_model()
        st.session_state.chat_session = model.start_chat(history=[])
    
    if "awaiting_info" not in st.session_state:
        st.session_state.awaiting_info = False
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Welcome message if no history
    if not st.session_state.messages:
        welcome_msg = """👋 **Welcome to Broadway Pizza Pakistan!**

I'm your AI ordering assistant. I can help you with:

🍕 **Browse Menu** - Pizzas, Wings, Pastas & more
🎁 **Check Deals** - Amazing combo offers
🛒 **Place Orders** - Quick & easy ordering
💳 **Payment Info** - Cash, Card, Mobile Wallets

What would you like to do today? Try saying:
• "Show me the menu"
• "What deals do you have?"
• "I want to order a pizza" """
        
        with st.chat_message("assistant"):
            st.markdown(welcome_msg)
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Check if we're awaiting customer info for order
                    if st.session_state.awaiting_info and st.session_state.cart:
                        name, phone = extract_customer_info(prompt)
                        if name and phone:
                            # Place the order
                            confirmation = save_order_to_db(name, phone, st.session_state.cart)
                            st.session_state.cart = []
                            st.session_state.awaiting_info = False
                            assistant_message = confirmation
                        else:
                            assistant_message = "I need both your **Name** and **Phone Number** to place the order. Please provide them like:\n\n*My name is Ali and phone is 03001234567*"
                    else:
                        # Process order intents (add to cart, view cart, etc.)
                        st.session_state.cart, order_response = process_order_intent(
                            prompt, 
                            st.session_state.cart
                        )
                        
                        if order_response:
                            assistant_message = order_response
                        else:
                            # Check for checkout intent
                            if any(word in prompt.lower() for word in ["checkout", "place order", "confirm", "finalize", "done ordering"]):
                                if st.session_state.cart:
                                    st.session_state.awaiting_info = True
                                    cart_display = format_cart_for_display(st.session_state.cart)
                                    assistant_message = f"{cart_display}\n\n✅ Great! To complete your order, please provide:\n\n👤 **Your Name**\n📱 **Phone Number**\n\n_Example: My name is Ali, phone 03001234567_"
                                else:
                                    assistant_message = "🛒 Your cart is empty! Please add some items first. Would you like to see our menu or deals?"
                            else:
                                # Get RAG context from database
                                context = detect_intent_and_get_context(prompt)
                                
                                # Add cart info to context if exists
                                if st.session_state.cart:
                                    context += f"\n\n**Current Cart:**\n{format_cart_for_display(st.session_state.cart)}"
                                
                                # Build message with context
                                if context:
                                    full_message = f"""**Context from database:**
{context}

**Customer message:** {prompt}

Please respond based on the context above. Be helpful and friendly!"""
                                else:
                                    full_message = prompt
                                
                                # Get response from Gemini
                                response = st.session_state.chat_session.send_message(full_message)
                                assistant_message = response.text
                    
                except Exception as e:
                    assistant_message = f"I apologize, but I encountered an error: {str(e)}. Please try again."
                
                st.markdown(assistant_message)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})


if __name__ == "__main__":
    main()
