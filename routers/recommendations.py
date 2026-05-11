from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from database import get_db
from bson import ObjectId
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

async def _build_corpus(db):
    """Fetch all books and build text corpus for TF-IDF using MongoDB Async."""
    books = await db.books.find().to_list(length=1000)
    
    corpus = []
    book_data = []
    for b in books:
        # NoSQL optimization: authors/categories are already in the document
        authors_str = b.get("authors", "")
        cats_str = b.get("categories", "")
        
        text = " ".join(filter(None, [
            b.get("summary") or "",
            cats_str,
            authors_str,
        ]))
        corpus.append(text)
        book_data.append({
            "id": str(b["_id"]),
            "name": b["name"],
            "authors": authors_str,
            "categories": cats_str,
            "stock": b.get("stock", 0)
        })
    return book_data, corpus

@router.get("/{book_id}", summary="Get similar book recommendations")
async def get_recommendations(
    book_id: str,
    top_n: int = Query(4, ge=1, le=10),
    db = Depends(get_db)
):
    books, corpus = await _build_corpus(db)
    book_ids = [b["id"] for b in books]

    if book_id not in book_ids:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    idx = book_ids.index(book_id)
    similarities = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

    similar_indices = similarities.argsort()[::-1]
    similar_indices = [i for i in similar_indices if i != idx][:top_n]

    recommendations = []
    for i in similar_indices:
        b = books[i]
        recommendations.append({
            "id": b["id"],
            "name": b["name"],
            "authors": b["authors"],
            "categories": b["categories"],
            "similarity_score": round(float(similarities[i]), 3),
        })

    source = next(b for b in books if b["id"] == book_id)
    return {
        "book": {"id": source["id"], "name": source["name"]},
        "recommendations": recommendations,
    }

@router.get("/for-customer/{customer_id}", summary="Personalized recommendations for a customer")
async def customer_recommendations(
    customer_id: str, 
    top_n: int = Query(5, ge=1, le=10),
    db = Depends(get_db)
):
    # Get books the customer has ordered or wishlisted
    orders = await db.orders.find({"customer_id": customer_id}).to_list(length=100)
    wishlist = await db.wishlist.find({"customer_id": customer_id}).to_list(length=100)
    
    seen_ids = set()
    for o in orders:
        for item in o.get("items", []):
            seen_ids.add(str(item.get("book_id")))
    for w in wishlist:
        seen_ids.add(str(w.get("book_id")))

    if not seen_ids:
        # Cold start: return featured books
        featured = await db.books.find({"featured": True}).limit(top_n).to_list(length=top_n)
        for b in featured:
            b["id"] = str(b.pop("_id"))
        return {"recommendations": featured, "based_on": "featured (no history)"}

    books, corpus = await _build_corpus(db)
    book_ids = [b["id"] for b in books]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    seen_indices = [book_ids.index(sid) for sid in seen_ids if sid in book_ids]
    if not seen_indices:
        return {"recommendations": [], "based_on": "no valid history found in corpus"}
        
    user_profile = np.mean(tfidf_matrix[seen_indices].toarray(), axis=0)
    scores = cosine_similarity([user_profile], tfidf_matrix).flatten()

    results = []
    for i in scores.argsort()[::-1]:
        b = books[i]
        if b["id"] not in seen_ids and b["stock"] > 0:
            results.append({
                "id": b["id"],
                "name": b["name"],
                "authors": b["authors"],
                "categories": b["categories"],
                "score": round(float(scores[i]), 3),
            })
        if len(results) >= top_n:
            break

    return {"recommendations": results, "based_on": f"customer {customer_id}'s history"}
