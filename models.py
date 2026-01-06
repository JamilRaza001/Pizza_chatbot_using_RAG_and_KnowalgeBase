"""
Broadway Pizza Chatbot - Data Models
=====================================
Pydantic models for data validation and serialization.
"""

import re
from typing import Optional, List
from pydantic import BaseModel, field_validator, Field

from config import PHONE_PATTERN, MIN_NAME_LENGTH, MAX_NAME_LENGTH


class CustomerInfo(BaseModel):
    """Validated customer information for orders."""
    name: str = Field(..., min_length=MIN_NAME_LENGTH, max_length=MAX_NAME_LENGTH)
    phone: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate customer name contains only letters and spaces."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty")
        if not all(c.isalpha() or c.isspace() for c in cleaned):
            raise ValueError("Name can only contain letters and spaces")
        return cleaned.title()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Pakistan phone number format."""
        # Remove spaces and dashes for normalization
        cleaned = v.replace(' ', '').replace('-', '')
        if not re.match(PHONE_PATTERN, cleaned):
            raise ValueError("Invalid phone number. Please use format: 03001234567")
        return cleaned
    
    def masked_phone(self) -> str:
        """Return phone with middle digits masked for privacy."""
        if len(self.phone) >= 7:
            return self.phone[:4] + "****" + self.phone[-3:]
        return self.phone


class CartItem(BaseModel):
    """A single item in the shopping cart."""
    name: str
    category: str
    base_price: float
    quantity: int = Field(default=1, ge=1, le=99)
    size: Optional[str] = None
    size_multiplier: float = Field(default=1.0)
    
    @property
    def unit_price(self) -> float:
        """Calculate price for one item including size multiplier."""
        return self.base_price * self.size_multiplier
    
    @property  
    def total_price(self) -> float:
        """Calculate total price for this cart item."""
        return self.unit_price * self.quantity
    
    def display_name(self) -> str:
        """Return formatted name with size if applicable."""
        if self.size:
            return f"{self.name} ({self.size})"
        return self.name


class Cart(BaseModel):
    """Shopping cart containing multiple items."""
    items: List[CartItem] = Field(default_factory=list)
    
    @property
    def total_items(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)
    
    @property
    def total_price(self) -> float:
        """Total price of all items in cart."""
        return sum(item.total_price for item in self.items)
    
    def add_item(self, item: CartItem) -> None:
        """Add an item to the cart. If same item+size exists, increase quantity."""
        for existing in self.items:
            if existing.name == item.name and existing.size == item.size:
                existing.quantity += item.quantity
                return
        self.items.append(item)
    
    def remove_item(self, index: int) -> Optional[CartItem]:
        """Remove item by index (1-based for user-friendly display)."""
        if 1 <= index <= len(self.items):
            return self.items.pop(index - 1)
        return None
    
    def update_quantity(self, index: int, quantity: int) -> bool:
        """Update quantity for item at index (1-based)."""
        if 1 <= index <= len(self.items) and 1 <= quantity <= 99:
            self.items[index - 1].quantity = quantity
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items from cart."""
        self.items.clear()
    
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0
    
    def to_order_json(self) -> list:
        """Convert cart to JSON-serializable format for order storage."""
        return [
            {
                "name": item.name,
                "category": item.category,
                "size": item.size,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            }
            for item in self.items
        ]


class MenuItem(BaseModel):
    """A menu item from the database."""
    id: str
    name: str
    category: str
    description: str
    sizes: Optional[str] = None
    base_price: float
    
    def get_price_for_size(self, size: str, multipliers: dict) -> float:
        """Calculate price for a specific size."""
        multiplier = multipliers.get(size, 1.0)
        return self.base_price * multiplier
