import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

async def get_user_preferences(db, user_id: str):
    """Fetch books the user has interacted with to build a profile."""
    # Combine purchases and wishlist
    orders = await db.orders.find({"customer_id": user_id}).to_list(length=100)
    wishlist = await db.wishlist.find({"customer_id": user_id}).to_list(length=100)
    
    seen_book_ids = set()
    for o in orders:
        for item in o.get("items", []):
            seen_book_ids.add(str(item.get("book_id")))
    for w in wishlist:
        seen_book_ids.add(str(w.get("book_id")))
        
    if not seen_book_ids:
        return None, set()

    # Fetch details of seen books to build the text profile
    # (Simplified: we use their combined text to build a single user vector)
    from bson import ObjectId
    books = await db.books.find({"_id": {"$in": [ObjectId(sid) for sid in seen_book_ids]}}).to_list(length=100)
    
    profile_text = ""
    for b in books:
        text = " ".join(filter(None, [
            b.get("summary") or "",
            b.get("categories") or "",
            b.get("authors") or "",
        ]))
        profile_text += " " + text
        
    return profile_text, seen_book_ids

async def apply_match_scores(db, books: List[Dict[str, Any]], user_id: str):
    """Calculate and append match_percentage to each book in the list."""
    profile_text, seen_ids = await get_user_preferences(db, user_id)
    if not profile_text:
        return books

    # We need a corpus to fit the vectorizer. 
    # For accuracy, we should use the same corpus the profile was built on, 
    # but for a quick page-view, we can use the current books + the profile.
    current_texts = []
    for b in books:
        text = " ".join(filter(None, [
            b.get("summary") or "",
            b.get("categories") or "",
            b.get("authors") or "",
        ]))
        current_texts.append(text)

    vectorizer = TfidfVectorizer(stop_words="english")
    # Fit on both profile and current books to ensure shared vocabulary
    all_texts = [profile_text] + current_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    user_vector = tfidf_matrix[0]
    book_vectors = tfidf_matrix[1:]
    
    similarities = cosine_similarity(user_vector, book_vectors).flatten()
    
    for i, b in enumerate(books):
        # Convert similarity (0-1) to percentage (0-100)
        # We add a slight boost for "featured" books to make it feel more Netflix-y
        score = similarities[i] * 100
        if b.get("featured"):
            score += 5
            
        # Ensure it's between 10 and 99 (never 100% to keep it realistic)
        final_score = int(min(99, max(10, score)))
        b["match_percentage"] = final_score
        
    return books
