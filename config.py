"""
Broadway Pizza Chatbot - Configuration
=======================================
Centralized configuration for the chatbot application.
"""

import logging
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "broadway_pizza.db"

# =============================================================================
# DATABASE SECURITY
# =============================================================================
# Whitelist of valid table names for safe DELETE operations
VALID_TABLES = frozenset({
    "restaurant_info",
    "menu_categories", 
    "menu_items",
    "deals",
    "dips",
    "crust_types",
    "orders",
    "chat_sessions",
    "chat_messages",
    "chat_summaries"
})

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

def setup_logging(name: str = __name__) -> logging.Logger:
    """Configure and return a logger instance."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )
    return logging.getLogger(name)

# =============================================================================
# PRICING CONFIGURATION
# =============================================================================
# Size multipliers for pizza pricing
SIZE_MULTIPLIERS = {
    "Small": 1.0,
    "Medium": 1.3,
    "Large": 1.6,
    "20-Inch Slice": 0.4  # Slice is ~40% of small price
}

# Crust extra prices
CRUST_PRICES = {
    "Thin Crust": 0,
    "Deep Pan": 100,
    "Stuffed Crust (King Crust)": 200
}

# =============================================================================
# VALIDATION
# =============================================================================
# Pakistan phone number regex pattern
PHONE_PATTERN = r'^(\+?92|0)?[-\s]?3\d{2}[-\s]?\d{7}$'

# Minimum/maximum name length
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
# Centralized LLM model names - change here to update everywhere
LLM_MODEL_NAME = "gemini-2.0-flash"
LLM_SUMMARIZATION_MODEL = "gemini-2.0-flash"  # Can be different if needed

# Retry configuration for API calls
LLM_MAX_RETRIES = 3
LLM_BASE_DELAY = 1.0  # seconds

# =============================================================================
# MEMORY CONFIGURATION
# =============================================================================
# Number of recent messages to keep raw (not summarized)
MEMORY_BUFFER_SIZE = 6
# Message count threshold to trigger summarization
MEMORY_SUMMARY_THRESHOLD = 10
