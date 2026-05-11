from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from schemas import OrderCreate, OrderResponse, MessageResponse
from routers.auth import get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate, 
    db = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    # 1. Validate books and stock
    order_items = []
    total_calculated = 0.0
    
    for item in order_in.items:
        if not ObjectId.is_valid(item.book_id):
            raise HTTPException(status_code=400, detail=f"Invalid book ID: {item.book_id}")
            
        book = await db.books.find_one({"_id": ObjectId(item.book_id)})
        if not book:
            raise HTTPException(status_code=404, detail=f"Book not found: {item.book_id}")
            
        if book["stock"] < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock for '{book['name']}'. Requested: {item.quantity}, Available: {book['stock']}"
            )
        
        # Dynamic Pricing Logic
        base_price = book["price"]
        item_price = base_price
        
        if item.format == "digital":
            item_price = base_price * 0.6  # 40% discount for PDF
        elif item.format == "both":
            item_price = base_price * 1.3  # 30% premium for both
        
        # Build the final item data
        order_items.append({
            "book_id": item.book_id,
            "book_name": book["name"],
            "quantity": item.quantity,
            "price": item_price,
            "format": item.format
        })
        total_calculated += item_price * item.quantity

    # 2. Create the order document
    order_doc = {
        "customer_id": str(current_user["_id"]),
        "customer_name": current_user["name"],
        "items": order_items,
        "total_amount": total_calculated,
        "status": "paid",
        "timestamp": datetime.utcnow()
    }

    # 3. Perform atomic-like updates (simplified)
    # In production, use MongoDB transactions for consistency
    result = await db.orders.insert_one(order_doc)
    
    # 4. Decrement stock
    for item in order_in.items:
        await db.books.update_one(
            {"_id": ObjectId(item.book_id)},
            {"$inc": {"stock": -item.quantity}}
        )

    return {"message": "Order placed successfully", "id": str(result.inserted_id)}

@router.get("/my-orders", response_model=list[OrderResponse])
async def get_my_orders(db = Depends(get_db), current_user: dict = Depends(get_current_user)):
    orders = await db.orders.find({"customer_id": str(current_user["_id"])}).sort("timestamp", -1).to_list(length=100)
    for o in orders:
        o["_id"] = str(o["_id"])
    return orders
