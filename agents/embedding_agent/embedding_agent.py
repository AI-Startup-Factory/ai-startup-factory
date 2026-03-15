import os
import requests
import random
from sentence_transformers import SentenceTransformer

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing Supabase environment variables")
    exit(1)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ==========================
# EMBEDDING MODEL OPTIONS
# ==========================

EMBED_MODELS = [
"nvidia/llama-nemotron-embed-vl-1b-v2:free",
"qwen/qwen3-embedding-0.6b"
]

LOCAL_MODEL = None


# ==========================
# FETCH ROWS
# ==========================

def fetch_rows():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&problem_embedding=is.null&limit=50"

    r = requests.get(url, headers=SUPABASE_HEADERS)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    data = r.json()

    print("Rows needing embedding:", len(data))

    return data


# ==========================
# OPENROUTER EMBEDDING
# ==========================

def embed_openrouter(texts):

    url = "https://openrouter.ai/api/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = EMBED_MODELS.copy()
    random.shuffle(models)

    for model in models:

        print("Trying embedding model:", model)

        payload = {
            "model": model,
            "input": texts
        }

        try:

            r = requests.post(url, headers=headers, json=payload, timeout=60)

            if r.status_code != 200:
                continue

            data = r.json()

            vectors = [d["embedding"] for d in data["data"]]

            return vectors

        except:
            continue

    return None


# ==========================
# LOCAL FALLBACK
# ==========================

def embed_local(texts):

    global LOCAL_MODEL

    if LOCAL_MODEL is None:

        print("Loading local embedding model...")

        LOCAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    vectors = LOCAL_MODEL.encode(texts)

    return [v.tolist() for v in vectors]


# ==========================
# VECTOR FORMAT FOR PGVECTOR
# ==========================

def vector_to_pg(v):

    return "[" + ",".join(str(x) for x in v) + "]"


# ==========================
# UPDATE ROW
# ==========================

def update_row(row_id, vector):

    payload = {
        "problem_embedding": vector_to_pg(vector)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=SUPABASE_HEADERS, json=payload)

    if r.status_code in [200, 204]:
        print("Updated embedding:", row_id)
    else:
        print("Update failed:", r.text)


# ==========================
# MAIN
# ==========================

def main():

    rows = fetch_rows()

    if not rows:
        print("No rows to process")
        return

    texts = [r["problem"] for r in rows]

    vectors = None

    if OPENROUTER_API_KEY:
        vectors = embed_openrouter(texts)

    if vectors is None:
        print("OpenRouter embedding failed, using local model")
        vectors = embed_local(texts)

    for row, vec in zip(rows, vectors):

        update_row(row["id"], vec)


if __name__ == "__main__":
    main()
