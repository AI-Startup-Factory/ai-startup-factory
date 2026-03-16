import math
import json
# Import core infrastructure
from core.config import settings
from core.database import db

# Threshold optimal untuk startup ideas
SIMILARITY_THRESHOLD = 0.88

def fetch_ideas_for_comparison():
    """
    Retrieves ideas that have embeddings and are not already marked as duplicates.
    """
    query = "problem_embedding=not.is.null&is_duplicate=eq.false&select=id,problem,problem_embedding&limit=1000"
    return db.fetch_records("ideas", query)

def cosine_similarity(a, b):
    """Calculates the cosine similarity between two vectors."""
    if len(a) != len(b): return 0
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0: return 0
    return dot_product / (norm_a * norm_b)

def mark_as_duplicate(duplicate_id, original_id):
    """Updates the record to mark it as a duplicate in the database."""
    payload = {
        "is_duplicate": True,
        "duplicate_of": original_id
    }
    return db.update_record("ideas", duplicate_id, payload)

def main():
    print("=== AI Startup Factory: Semantic Deduplicator Agent ===")
    
    raw_ideas = fetch_ideas_for_comparison()
    if len(raw_ideas) < 2:
        print("✅ Not enough ideas to perform comparison.")
        return

    processed_ideas = []
    for item in raw_ideas:
        vec = item.get("problem_embedding")
        if vec and isinstance(vec, list):
            processed_ideas.append({
                "id": item["id"],
                "vector": vec,
                "problem_snippet": item.get("problem", "")[:60].replace("\n", " ")
            })

    print(f"📡 Analyzing {len(processed_ideas)} potential ideas for overlaps...")

    duplicate_count = 0
    marked_ids = set()

    for i in range(len(processed_ideas)):
        idea_a = processed_ideas[i]
        if idea_a["id"] in marked_ids: continue
        
        for j in range(i + 1, len(processed_ideas)):
            idea_b = processed_ideas[j]
            if idea_b["id"] in marked_ids: continue
            
            similarity = cosine_similarity(idea_a["vector"], idea_b["vector"])

            if similarity >= SIMILARITY_THRESHOLD:
                print(f"🔥 DUPLICATE: [{similarity:.4f}]")
                print(f"   Original: {idea_a['problem_snippet']}")
                print(f"   Duplicate: {idea_b['problem_snippet']}")
                
                if mark_as_duplicate(idea_b["id"], idea_a["id"]):
                    marked_ids.add(idea_b["id"])
                    duplicate_count += 1

    print(f"✅ Deduplication complete. Marked {duplicate_count} records.")

if __name__ == "__main__":
    main()
