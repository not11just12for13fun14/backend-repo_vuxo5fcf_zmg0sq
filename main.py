import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product, Service, Gig

app = FastAPI(title="Marketplace API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Marketplace Backend Running"}

# ----------------------------
# Health & Schema
# ----------------------------

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# ----------------------------
# Seed endpoint (optional)
# ----------------------------

class SeedRequest(BaseModel):
    force: bool = False

@app.post("/seed")
def seed_data(payload: SeedRequest):
    # Only seed if collections are empty or force=True
    collections = {
        "product": db["product"].count_documents({}) if db else 0,
        "service": db["service"].count_documents({}) if db else 0,
        "gig": db["gig"].count_documents({}) if db else 0,
    }
    if not payload.force and any(count > 0 for count in collections.values()):
        return {"status": "skipped", "reason": "Collections already contain data", "counts": collections}

    # Example curated items
    products = [
        Product(title="Minimalist Desk Lamp", description="Warm LED lamp with matte finish", price=59.0, category="Home", image="https://images.unsplash.com/photo-1507473885765-e6ed057f782c", tags=["lighting","desk"], curated=True),
        Product(title="Ergonomic Chair", description="Breathable mesh back", price=199.0, category="Office", image="https://images.unsplash.com/photo-1503602642458-232111445657", tags=["chair","office"], curated=True),
        Product(title="Stoneware Mug", description="Hand‑thrown, dishwasher safe", price=24.0, category="Kitchen", image="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd", tags=["mug","ceramic"], curated=True),
    ]
    services = [
        Service(title="Brand Design Sprint", description="1-week intensive brand refresh", price=1200, category="Design", provider="Top Studio", image="https://images.unsplash.com/photo-1526948128573-703ee1aeb6fa", tags=["branding","design"], curated=True),
        Service(title="Landing Page Build", description="High-converting responsive page", price=800, category="Development", provider="Web Pro", image="https://images.unsplash.com/photo-1498050108023-c5249f4df085", tags=["web","react"], curated=True),
        Service(title="Product Photography Pack", description="15 retouched shots", price=450, category="Photography", provider="Studio Light", image="https://images.unsplash.com/photo-1487412720507-e7ab37603c6f", tags=["photo","ecommerce"], curated=True),
    ]
    gigs = [
        Gig(title="Event Photographer", description="4-hour evening shoot", pay=350, pay_type="fixed", category="Photography", company="Local Events", location="On-site", remote=False, tags=["photo","event"]),
        Gig(title="Figma to React", description="Convert 5 screens", pay=45, pay_type="hourly", category="Development", company="Startup X", remote=True, tags=["react","frontend"]),
        Gig(title="Shopify Setup Assistant", description="Configure theme and payments", pay=30, pay_type="hourly", category="Ecommerce", company="Indie Brand", remote=True, tags=["shopify","store"]),
    ]

    inserted = {"products": 0, "services": 0, "gigs": 0}
    try:
        for p in products:
            create_document("product", p)
            inserted["products"] += 1
        for s in services:
            create_document("service", s)
            inserted["services"] += 1
        for g in gigs:
            create_document("gig", g)
            inserted["gigs"] += 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")

    return {"status": "ok", "inserted": inserted}

# ----------------------------
# Public listing endpoints with search
# ----------------------------


def build_search_query(base: dict, q: Optional[str]):
    if q:
        regex = {"$regex": q, "$options": "i"}
        # add OR conditions common for most collections
        base["$or"] = [
            {"title": regex},
            {"description": regex},
            {"category": regex},
            {"tags": regex},  # tags is an array; regex works on array elements in Mongo
        ]
    return base


@app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = None, curated: Optional[bool] = None, q: Optional[str] = None):
    query: dict = {}
    if category:
        query["category"] = category
    if curated is not None:
        query["curated"] = curated
    query = build_search_query(query, q)
    try:
        docs = get_documents("product", query, limit=50)
        for d in docs:
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/services", response_model=List[Service])
def list_services(category: Optional[str] = None, curated: Optional[bool] = None, q: Optional[str] = None):
    query: dict = {}
    if category:
        query["category"] = category
    if curated is not None:
        query["curated"] = curated
    # also include provider/company fields in search using build then extend
    query = build_search_query(query, q)
    if q:
        regex = {"$regex": q, "$options": "i"}
        # ensure provider is considered as well
        query.setdefault("$or", []).append({"provider": regex})
    try:
        docs = get_documents("service", query, limit=50)
        for d in docs:
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gigs", response_model=List[Gig])
def list_gigs(category: Optional[str] = None, remote: Optional[bool] = None, q: Optional[str] = None):
    query: dict = {}
    if category:
        query["category"] = category
    if remote is not None:
        query["remote"] = remote
    query = build_search_query(query, q)
    if q:
        regex = {"$regex": q, "$options": "i"}
        query.setdefault("$or", []).extend([
            {"company": regex},
            {"location": regex},
        ])
    try:
        docs = get_documents("gig", query, limit=50)
        for d in docs:
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
