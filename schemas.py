from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from typing import Optional, List, Annotated
from datetime import datetime

# Helper to handle MongoDB ObjectId as a string
PyObjectId = Annotated[str, BeforeValidator(str)]

# ─── BOOK ────────────────────────────────────────────────────

class BookBase(BaseModel):
    name: str
    summary: Optional[str] = None
    price: float
    stock: int = 0
    edition: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    featured: bool = False
    pdf_url: Optional[str] = None

class BookCreate(BookBase):
    author_ids: Optional[List[int]] = []
    category_ids: Optional[List[int]] = []

class BookUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    featured: Optional[bool] = None
    summary: Optional[str] = None

class BookResponse(BookBase):
    id: PyObjectId = Field(alias="_id") # Mapping MongoDB _id to id
    authors: Optional[str] = None      
    categories: Optional[str] = None
    match_percentage: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True, # allows using 'id' in code but '_id' in data
    )

# ─── WRITER (Author) ─────────────────────────────────────────

class WriterBase(BaseModel):
    name: str
    about: Optional[str] = None

class WriterCreate(WriterBase):
    pass

class WriterResponse(WriterBase):
    id: PyObjectId = Field(alias="_id")
    books: Optional[List[str]] = []   

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ─── CATEGORY ────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    book_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ─── CUSTOMER ────────────────────────────────────────────────

class CustomerResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ─── USER AUTH ───────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ─── REVIEW ──────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    book_id: str
    customer_id: str
    rating: int = Field(ge=1, le=5)
    statement: Optional[str] = None

class ReviewResponse(ReviewCreate):
    id: PyObjectId = Field(alias="_id")
    timestamp: str
    book_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ─── COMMON RESPONSES ────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None

# ─── ORDERS ──────────────────────────────────────────────────

class OrderItem(BaseModel):
    book_id: str
    book_name: Optional[str] = None
    quantity: int = Field(gt=0)
    price: float # Price at the time of order
    format: str = "digital" # "digital" or "physical"

class OrderCreate(BaseModel):
    items: List[OrderItem]
    total_amount: float

class OrderResponse(OrderCreate):
    id: PyObjectId = Field(alias="_id")
    customer_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PaginatedBooks(BaseModel):
    total: int
    page: int
    per_page: int
    books: List[BookResponse]
