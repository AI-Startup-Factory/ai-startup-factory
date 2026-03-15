import os
import requests
from sentence_transformers import SentenceTransformer

from agents.utils.vector_projection import project_vector


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Loading local embedding model...")

local_model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------------------------------
# FETCH IDEAS WITHOUT EMBEDDING
# -------------------------------------------------

def fetch_rows():

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    params = {
        "select":"id,problem",
        "problem_embedding":"is.null",
        "limit":50
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:

        print("Fetch error:", r.text)

        return []

    data = r.json()

    print("Rows needing embedding:", len(data))

    return data


# -------------------------------------------------
# LOCAL EMBEDDING
# -------------------------------------------------

def embed_local(text):

    vec = local_model.encode(text)

    return vec.tolist()


# -------------------------------------------------
# OPENROUTER EMBEDDING
# -------------------------------------------------

def embed_openrouter(text):

    r = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model":"qwen/qwen3-embedding-0.6b",
            "input":text
        },
        timeout=30
    )

    if r.status_code != 200:

        raise Exception("OpenRouter embedding failed")

    data = r.json()

    return data["data"][0]["embedding"]


# -------------------------------------------------
# VECTOR TO POSTGRES FORMAT
# -------------------------------------------------

def vector_to_pg(v):

    return "[" + ",".join(str(x) for x in v) + "]"


# -------------------------------------------------
# UPDATE ROW
# -------------------------------------------------

def update_row(row_id, vector):

    payload = {
        "problem_embedding": vector_to_pg(vector)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200,204]:

        print("Updated embedding:", row_id)

    else:

        print("Update failed:", r.text)


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    rows = fetch_rows()

    if not rows:

        print("No rows to process")

        return

    for row in rows:

        text = row["problem"]

        try:

            # primary embedding (local)
            vec = embed_local(text)

        except Exception:

            print("Local embedding failed, using OpenRouter")

            vec = embed_openrouter(text)

        # projection to 384 dimension
        vec = project_vector(vec)

        update_row(row["id"], vec)


if __name__ == "__main__":
    main()
