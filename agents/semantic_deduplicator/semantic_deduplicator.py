import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

SIMILARITY_THRESHOLD = 0.88

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# ============================
# FETCH IDEAS WITH EMBEDDING
# ============================

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,idea,problem_embedding&problem_embedding=not.is.null"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# ============================
# COSINE SIMILARITY
# ============================

def cosine_similarity(a, b):

    dot = sum(x*y for x, y in zip(a, b))

    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5

    return dot / (norm_a * norm_b)


# ============================
# PARSE PGVECTOR
# ============================

def parse_vector(v):

    v = v.strip("[]")

    return [float(x) for x in v.split(",")]


# ============================
# MARK DUPLICATE
# ============================

def mark_duplicate(idea_id, original_id):

    payload = {
        "is_duplicate": True,
        "duplicate_of": original_id
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Marked duplicate:", idea_id)
    else:
        print("Update failed:", r.text)


# ============================
# MAIN ENGINE
# ============================

def main():

    ideas = fetch_ideas()

    if len(ideas) < 2:
        print("Not enough ideas")
        return

    vectors = {}

    for i in ideas:

        vectors[i["id"]] = parse_vector(i["problem_embedding"])

    checked = set()

    for idea_a in ideas:

        id_a = idea_a["id"]

        if id_a in checked:
            continue

        vec_a = vectors[id_a]

        for idea_b in ideas:

            id_b = idea_b["id"]

            if id_a == id_b:
                continue

            vec_b = vectors[id_b]

            sim = cosine_similarity(vec_a, vec_b)

            if sim > SIMILARITY_THRESHOLD:

                mark_duplicate(id_b, id_a)

        checked.add(id_a)


if __name__ == "__main__":
    main()
