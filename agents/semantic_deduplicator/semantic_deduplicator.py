import os
import requests
import math
import json
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

SIMILARITY_THRESHOLD = 0.88

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# ==========================================
# FETCH IDEAS WITH EMBEDDINGS
# ==========================================

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    params = {
        "select": "id,problem,problem_embedding,is_duplicate",
        "problem_embedding": "not.is.null",
        "is_duplicate": "eq.false",
        "limit": 5000
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# ==========================================
# VECTOR PARSER
# ==========================================

def parse_vector(v):

    if v is None:
        return None

    if isinstance(v, list):
        return v

    try:
        v = v.strip("[]")
        return [float(x) for x in v.split(",")]
    except:
        return None


# ==========================================
# COSINE SIMILARITY
# ==========================================

def cosine_similarity(a, b):

    if len(a) != len(b):
        return 0

    dot = sum(x*y for x, y in zip(a, b))

    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0

    return dot / (norm_a * norm_b)


# ==========================================
# MARK DUPLICATE
# ==========================================

def mark_duplicate(duplicate_id, original_id):

    payload = {
        "is_duplicate": True,
        "duplicate_of": original_id
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{duplicate_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print(f"Duplicate {duplicate_id} -> {original_id}")
    else:
        print("Update failed:", r.text)


# ==========================================
# MAIN ENGINE
# ==========================================

def main():

    print("Running Semantic Deduplicator")

    ideas = fetch_ideas()

    print("Ideas fetched:", len(ideas))

    if len(ideas) < 2:
        print("Not enough ideas")
        return

    vectors = {}

    for i in ideas:

        vec = parse_vector(i.get("problem_embedding"))

        if vec:
            vectors[i["id"]] = vec

    ids = list(vectors.keys())

    checked = set()

    duplicates = 0

    for i in range(len(ids)):

        id_a = ids[i]

        if id_a in checked:
            continue

        vec_a = vectors[id_a]

        for j in range(i+1, len(ids)):

            id_b = ids[j]

            if id_b in checked:
                continue

            vec_b = vectors[id_b]

            sim = cosine_similarity(vec_a, vec_b)

            if sim >= SIMILARITY_THRESHOLD:

                mark_duplicate(id_b, id_a)

                checked.add(id_b)

                duplicates += 1

        checked.add(id_a)

        if i % 50 == 0:
            print("Progress:", i, "/", len(ids))

    print("Total duplicates:", duplicates)
    print("Semantic deduplication finished")


if __name__ == "__main__":
    main()
