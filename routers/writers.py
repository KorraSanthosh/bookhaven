from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db
from schemas import WriterCreate, WriterResponse, MessageResponse
from bson import ObjectId

router = APIRouter(prefix="/writers", tags=["Writers"])

@router.get("/", response_model=List[WriterResponse], summary="List all authors")
async def list_writers(db = Depends(get_db)):
    writers = await db.writers.find().sort("name", 1).to_list(length=100)
    return writers

@router.get("/{writer_id}", response_model=WriterResponse, summary="Get a single author")
async def get_writer(writer_id: str, db = Depends(get_db)):
    if not ObjectId.is_valid(writer_id):
        raise HTTPException(status_code=400, detail="Invalid writer ID format")
        
    writer = await db.writers.find_one({"_id": ObjectId(writer_id)})
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    return writer

@router.post("/", response_model=MessageResponse, status_code=201, summary="Add a new author")
async def create_writer(writer_in: WriterCreate, db = Depends(get_db)):
    writer_dict = writer_in.model_dump()
    result = await db.writers.insert_one(writer_dict)
    return {"message": "Writer created", "id": str(result.inserted_id)}
