"""
Database Schemas for Restaurant Ordering App

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., MenuItem -> "menuitem").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Core domain models

class MenuItem(BaseModel):
    """
    Restaurant menu items
    Collection: "menuitem"
    """
    name: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description of the dish")
    price: float = Field(..., ge=0, description="Unit price in dollars")
    category: str = Field(..., description="Category such as Starters, Mains, Drinks, Desserts")
    image_url: Optional[str] = Field(None, description="Optional image URL for the dish")
    is_available: bool = Field(True, description="Whether the dish is currently available")

class OrderItem(BaseModel):
    menu_item_id: str = Field(..., description="ID of the MenuItem as string")
    name: str = Field(..., description="Snapshot of menu item name at order time")
    unit_price: float = Field(..., ge=0, description="Snapshot price at order time")
    quantity: int = Field(..., ge=1, description="Number of units ordered")
    notes: Optional[str] = Field(None, description="Special instructions for this item")

class Customer(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class Order(BaseModel):
    """
    Customer orders
    Collection: "order"
    """
    customer: Customer
    items: List[OrderItem]
    subtotal: float = Field(..., ge=0)
    tax: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="pending | confirmed | preparing | ready | completed | cancelled")
    table_number: Optional[str] = Field(None, description="Optional table number for dine-in")
    pickup: bool = Field(False, description="True for pickup/takeout orders")
