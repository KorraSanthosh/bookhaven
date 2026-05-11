from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from database import get_db
from schemas import BookCreate, BookUpdate, BookResponse, MessageResponse, PaginatedBooks, ReviewResponse
from routers.auth import get_current_user
from bson import ObjectId

from services.recommender import apply_match_scores

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/", response_model=PaginatedBooks, summary="List all books")
async def list_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    search: str = Query(None),
    featured: bool = Query(None),
    in_stock: bool = Query(None),
    user_id: str = Query(None), # Optional user ID for Netflix-style matching
    db = Depends(get_db)
):
    query = {}
    if category:
        query["categories"] = {"$regex": category, "$options": "i"} # case-insensitive regex
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if featured is not None:
        query["featured"] = featured
    if in_stock:
        query["stock"] = {"$gt": 0}

    cursor = db.books.find(query)
    total = await db.books.count_documents(query)
    
    cursor.skip((page - 1) * per_page).limit(per_page)
    books = await cursor.to_list(length=per_page)

    # Apply personalized match scores if user_id is provided
    if user_id:
        books = await apply_match_scores(db, books, user_id)
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "books": books # Pydantic alias will handle _id -> id mapping
    }

@router.get("/{book_id}", response_model=BookResponse, summary="Get a single book")
async def get_book(book_id: str, db = Depends(get_db)):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/filter/featured", response_model=List[BookResponse], summary="Featured books")
async def get_featured_books(db = Depends(get_db)):
    books = await db.books.find({"featured": True}).to_list(length=100)
    return books

@router.get("/{book_id}/reviews", response_model=List[ReviewResponse], summary="Get reviews for a book")
async def get_book_reviews(book_id: str, db = Depends(get_db)):
    reviews = await db.reviews.find({"book_id": book_id}).sort("timestamp", -1).to_list(length=100)
    return reviews

@router.post("/", response_model=MessageResponse, status_code=201, summary="Add a new book")
async def create_book(book_in: BookCreate, db = Depends(get_db)):
    book_dict = book_in.model_dump()
    result = await db.books.insert_one(book_dict)
    return {"message": "Book created successfully", "id": str(result.inserted_id)}

@router.patch("/{book_id}", response_model=MessageResponse, summary="Update a book")
async def update_book(book_id: str, updates: BookUpdate, db = Depends(get_db)):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    
    update_data = {k: v for k, v in updates.model_dump(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book updated", "id": book_id}

@router.delete("/{book_id}", response_model=MessageResponse, summary="Delete a book")
async def delete_book(book_id: str, db = Depends(get_db)):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=400, detail="Invalid book ID format")
        
    result = await db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted", "id": book_id}

@router.get("/{book_id}/read", summary="Get reading access to a book")
async def read_book(
    book_id: str, 
    db = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    
    # Check if user has purchased the book in digital format
    order = await db.orders.find_one({
        "customer_id": str(current_user["_id"]),
        "items": {
            "$elemMatch": {
                "book_id": book_id,
                "format": "digital"
            }
        }
    })
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Digital access required. If you purchased a physical copy, please upgrade to digital to read in-app."
        )
    
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book or not book.get("pdf_url"):
        # Fallback for demo: if no PDF is assigned, provide a sample
        sample_pdf = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        return {"pdf_url": sample_pdf, "title": book.get("name") if book else "Unknown"}
    
    return {"pdf_url": book["pdf_url"], "title": book["name"]}
