import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import MenuItem, Order, OrderItem, Customer

app = FastAPI(title="Restaurant Ordering API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Restaurant API is running"}


@app.get("/test")
def test_database():
    """Test endpoint to check DB connectivity and list first collections"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "collections": [],
    }
    try:
        if db is not None:
            collections = db.list_collection_names()
            response["database"] = "✅ Connected"
            response["collections"] = collections[:10]
        else:
            response["database"] = "❌ Not Configured"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# -------- Menu Endpoints --------

@app.get("/api/menu", response_model=List[MenuItem])
def get_menu():
    items = get_documents("menuitem")
    return [
        MenuItem(
            name=i.get("name"),
            description=i.get("description"),
            price=i.get("price", 0.0),
            category=i.get("category", "Other"),
            image_url=i.get("image_url"),
            is_available=i.get("is_available", True),
        )
        for i in items
    ]


@app.post("/api/menu", status_code=201)
def add_menu_item(item: MenuItem):
    try:
        new_id = create_document("menuitem", item)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/menu/seed")
def seed_menu():
    """Seed the database with a small sample menu if empty."""
    try:
        existing = db["menuitem"].count_documents({}) if db is not None else 0
        if existing > 0:
            return {"inserted": 0, "message": "Menu already populated"}
        samples = [
            {
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato, mozzarella, basil",
                "price": 10.99,
                "category": "Mains",
                "image_url": "https://images.unsplash.com/photo-1548365328-9f547fb0953c",
                "is_available": True,
            },
            {
                "name": "Caesar Salad",
                "description": "Romaine, parmesan, croutons, caesar dressing",
                "price": 8.5,
                "category": "Starters",
                "image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141",
                "is_available": True,
            },
            {
                "name": "Spaghetti Bolognese",
                "description": "Rich beef ragu over spaghetti",
                "price": 13.25,
                "category": "Mains",
                "image_url": "https://images.unsplash.com/photo-1523986371872-9d3ba2e2a389",
                "is_available": True,
            },
            {
                "name": "Lemonade",
                "description": "Freshly squeezed lemonade",
                "price": 3.75,
                "category": "Drinks",
                "image_url": "https://images.unsplash.com/photo-1497534446932-c925b458314e",
                "is_available": True,
            },
            {
                "name": "Chocolate Brownie",
                "description": "Warm brownie with vanilla ice cream",
                "price": 6.0,
                "category": "Desserts",
                "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476e",
                "is_available": True,
            },
        ]
        inserted = 0
        for s in samples:
            create_document("menuitem", s)
            inserted += 1
        return {"inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------- Order Endpoints --------

class CreateOrderRequest(BaseModel):
    customer: Customer
    items: List[OrderItem]
    table_number: Optional[str] = None
    pickup: bool = False


@app.post("/api/orders", status_code=201)
def create_order(payload: CreateOrderRequest):
    # Compute totals server-side for integrity
    subtotal = sum(oi.unit_price * oi.quantity for oi in payload.items)
    tax = round(subtotal * 0.08, 2)  # 8% sample tax
    total = round(subtotal + tax, 2)

    order_doc = Order(
        customer=payload.customer,
        items=payload.items,
        subtotal=round(subtotal, 2),
        tax=tax,
        total=total,
        status="pending",
        table_number=payload.table_number,
        pickup=payload.pickup,
    )

    try:
        new_id = create_document("order", order_doc)
        return {"id": new_id, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders")
def list_orders(limit: int = 50):
    try:
        docs = get_documents("order", limit=limit)
        # Map ObjectId to string for frontend consumption
        def map_order(doc):
            doc["id"] = str(doc.get("_id"))
            doc.pop("_id", None)
            return doc
        return [map_order(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
