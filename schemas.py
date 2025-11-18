"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- Service -> "service" collection
- Gig -> "gig" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# ----------------------------
# Core Marketplace Schemas
# ----------------------------

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    image: Optional[HttpUrl] = Field(None, description="Image URL")
    rating: Optional[float] = Field(4.5, ge=0, le=5, description="Average rating")
    curated: bool = Field(True, description="Whether item is curated")
    tags: Optional[List[str]] = Field(default_factory=list, description="Searchable tags")
    in_stock: bool = Field(True, description="Whether product is in stock")

class Service(BaseModel):
    """
    Services collection schema
    Collection name: "service"
    """
    title: str = Field(..., description="Service title")
    description: Optional[str] = Field(None, description="Service description")
    price: float = Field(..., ge=0, description="Base price")
    category: str = Field(..., description="Service category")
    provider: Optional[str] = Field(None, description="Provider name")
    image: Optional[HttpUrl] = Field(None, description="Image URL")
    rating: Optional[float] = Field(4.6, ge=0, le=5)
    curated: bool = Field(True)
    tags: Optional[List[str]] = Field(default_factory=list)

class Gig(BaseModel):
    """
    Gig jobs collection schema
    Collection name: "gig"
    """
    title: str = Field(..., description="Gig title")
    description: Optional[str] = Field(None)
    pay: float = Field(..., ge=0, description="Hourly or fixed pay")
    pay_type: str = Field("fixed", description="'fixed' or 'hourly'")
    category: str = Field(...)
    company: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    remote: bool = Field(True)
    tags: Optional[List[str]] = Field(default_factory=list)

# Optional: simple user to extend later
class User(BaseModel):
    name: str
    email: str
    is_active: bool = True
