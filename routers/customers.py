from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db
from schemas import CustomerResponse
from bson import ObjectId

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/", response_model=List[CustomerResponse], summary="List all customers")
async def list_customers(db = Depends(get_db)):
    customers = await db.customers.find().to_list(length=100)
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse, summary="Get a customer")
async def get_customer(customer_id: str, db = Depends(get_db)):
    if not ObjectId.is_valid(customer_id):
        raise HTTPException(status_code=400, detail="Invalid customer ID format")
        
    customer = await db.customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/{customer_id}/orders", summary="Get all orders for a customer")
async def get_customer_orders(customer_id: str, db = Depends(get_db)):
    orders = await db.orders.find({"customer_id": customer_id}).sort("timestamp", -1).to_list(length=100)
    for o in orders:
        o["_id"] = str(o["_id"])
    return orders

@router.get("/{customer_id}/wishlist", summary="Get wishlist for a customer")
async def get_wishlist(customer_id: str, db = Depends(get_db)):
    wishlist = await db.wishlist.find({"customer_id": customer_id}).to_list(length=100)
    # Fetch book details for each wishlist item
    result = []
    for item in wishlist:
        book = await db.books.find_one({"_id": ObjectId(item["book_id"])})
        if book:
            result.append({
                "id": str(book["_id"]),
                "name": book["name"],
                "price": book["price"],
                "stock": book["stock"],
                "authors": book.get("authors", "")
            })
    return result

@router.get("/{customer_id}/reviews", summary="Get reviews by a customer")
async def get_customer_reviews(customer_id: str, db = Depends(get_db)):
    reviews = await db.reviews.find({"customer_id": customer_id}).sort("timestamp", -1).to_list(length=100)
    for r in reviews:
        r["_id"] = str(r["_id"])
        # Fetch book name
        book = await db.books.find_one({"_id": ObjectId(r["book_id"])})
        r["book_name"] = book["name"] if book else "Unknown Book"
    return reviews
