import os
import requests
from sentence_transformers import SentenceTransformer

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing environment variables")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


def fetch_rows():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&problem_embedding=is.null&limit=50"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    data = r.json()

    print("Rows needing embedding:", len(data))

    return data


def embed(texts):

    vectors = model.encode(texts)

    return [v.tolist() for v in vectors]


def vector_to_pg(v):

    return "[" + ",".join(str(x) for x in v) + "]"


def update_row(row_id, vector):

    payload = {
        "problem_embedding": vector_to_pg(vector)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Updated embedding:", row_id)
    else:
        print("Update failed:", r.text)


def main():

    rows = fetch_rows()

    if not rows:
        print("No rows to process")
        return

    texts = [r["problem"] for r in rows]

    embeddings = embed(texts)

    for row, vec in zip(rows, embeddings):

        update_row(row["id"], vec)


if __name__ == "__main__":
    main()
