import os
import requests
import math
import json
import time

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Threshold 0.88 - 0.92 adalah sweet spot untuk startup ideas
SIMILARITY_THRESHOLD = 0.88

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ==========================================
# FETCH IDEAS WITH EMBEDDINGS
# ==========================================
def fetch_ideas():
    url = f"{SUPABASE_URL}/rest/v1/ideas"
    
    # Kita hanya mengambil yang sudah ada embedding dan bukan duplikat yang sudah diketahui
    params = {
        "select": "id,problem,problem_embedding",
        "problem_embedding": "not.is.null",
        "is_duplicate": "eq.false",
        "limit": 1000 # Limit batch per run agar tidak timeout di GitHub Actions
    }

    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            print(f"Fetch error: {r.text}")
            return []
        return r.json()
    except Exception as e:
        print(f"Connection error: {e}")
        return []

# ==========================================
# VECTOR PARSER (Robust for pgvector strings)
# ==========================================
def parse_vector(v):
    if v is None: return None
    if isinstance(v, list): return v
    
    # Supabase kadang mengembalikan string "[0.1, 0.2, ...]"
    if isinstance(v, str):
        try:
            return json.loads(v)
        except:
            try:
                v = v.strip("[]").split(",")
                return [float(x) for x in v]
            except:
                return None
    return None

# ==========================================
# COSINE SIMILARITY (Optimized)
# ==========================================
def cosine_similarity(a, b):
    if len(a) != len(b): return 0
    
    dot_product = 0
    norm_a = 0
    norm_b = 0
    
    for x, y in zip(a, b):
        dot_product += x * y
        norm_a += x * x
        norm_b += y * y
        
    if norm_a == 0 or norm_b == 0: return 0
    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

# ==========================================
# MARK DUPLICATE
# ==========================================
def mark_duplicate(duplicate_id, original_id):
    payload = {
        "is_duplicate": True,
        "duplicate_of": original_id
    }
    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{duplicate_id}"
    try:
        r = requests.patch(url, headers=headers, json=payload)
        return r.status_code in [200, 204]
    except:
        return False

# ==========================================
# MAIN ENGINE
# ==========================================
def main():
    print("=== Running Semantic Deduplicator ===")
    
    ideas = fetch_ideas()
    if len(ideas) < 2:
        print("Not enough new ideas to compare.")
        return

    # Pre-parse vectors to save CPU cycles
    processed_data = []
    for i in ideas:
        vec = parse_vector(i.get("problem_embedding"))
        if vec:
            processed_data.append({
                "id": i["id"],
                "vector": vec,
                "problem": i.get("problem", "")[:50]
            })

    print(f"Comparing {len(processed_data)} ideas...")

    duplicate_count = 0
    already_marked = set()

    for i in range(len(processed_data)):
        id_a = processed_data[i]["id"]
        if id_a in already_marked: continue
        
        vec_a = processed_data[i]["vector"]

        for j in range(i + 1, len(processed_data)):
            id_b = processed_data[j]["id"]
            if id_b in already_marked: continue
            
            vec_b = processed_data[j]["vector"]
            
            similarity = cosine_similarity(vec_a, vec_b)

            if similarity >= SIMILARITY_THRESHOLD:
                print(f"MATCH FOUND: '{processed_data[i]['problem']}' ≈ '{processed_data[j]['problem']}' (Sim: {similarity:.4f})")
                
                if mark_duplicate(id_b, id_a):
                    already_marked.add(id_b)
                    duplicate_count += 1

    print(f"Deduplication finished. Found and marked {duplicate_count} duplicates.")

if __name__ == "__main__":
    main()
