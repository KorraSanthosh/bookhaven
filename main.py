"""
main.py
-------
BookHaven FastAPI - Professional Version (MongoDB Atlas)

Run the app:
    python3 -m uvicorn main:app --reload
"""

from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Import database session dependency
from database import get_db

# Import all routers
from routers.books import router as books_router
from routers.writers import router as writers_router
from routers.categories import router as categories_router
from routers.customers import router as customers_router
from routers.recommendations import router as reco_router
from routers.auth import router as auth_router
from routers.orders import router as orders_router

# ─── App Setup ───────────────────────────────────────────────
app = FastAPI(
    title="BookHaven API (MongoDB Pro)",
    description="""
BookHaven online bookstore API — professionally powered by MongoDB Atlas.

## Features
- **MongoDB Atlas** for scalable, cloud-native storage.
- **Async Motor Client** for high-performance I/O.
- **Pydantic v2** validation with ObjectId mapping.
- **AI Recommendations** via scikit-learn.
    """,
    version="4.0.0",
)

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files (frontend) ──────────────────────────────────
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# ─── Register Routers ─────────────────────────────────────────
app.include_router(books_router,      prefix="/api")
app.include_router(writers_router,    prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(customers_router,  prefix="/api")
app.include_router(reco_router,       prefix="/api")
app.include_router(auth_router,       prefix="/api")
app.include_router(orders_router,     prefix="/api")

# ─── Root Endpoint ────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "app": "BookHaven API",
        "version": "4.0.0",
        "framework": "FastAPI with MongoDB Atlas",
        "docs": "/docs",
        "endpoints": {
            "books":           "/api/books/",
            "writers":         "/api/writers/",
            "categories":      "/api/categories/",
            "customers":       "/api/customers/",
            "recommendations": "/api/recommendations/{book_id}",
        }
    }

# ─── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["Root"])
async def health(db = Depends(get_db)):
    try:
        # Check MongoDB connectivity by counting books
        count = await db.books.count_documents({})
        return {"status": "ok", "backend": "mongodb", "books_in_db": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ─── Run directly ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
