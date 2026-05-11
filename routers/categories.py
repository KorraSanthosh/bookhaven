from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db
from schemas import CategoryResponse
from bson import ObjectId

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse], summary="List all categories")
async def list_categories(db = Depends(get_db)):
    # Simple list for now; in a real NoSQL setup, book_count might be cached or aggregated
    categories = await db.categories.find().sort("name", 1).to_list(length=100)
    return categories

@router.get("/{name}/books", summary="Get books in a category")
async def books_by_category(name: str, db = Depends(get_db)):
    query = {"categories": {"$regex": name, "$options": "i"}}
    books = await db.books.find(query).to_list(length=100)
    # Convert _id to id for each book
    for b in books:
        b["_id"] = str(b["_id"])
    return {"category": name, "books": books}
