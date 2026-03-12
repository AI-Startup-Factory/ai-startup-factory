import os
import math
import requests
import numpy as np
from sklearn.cluster import KMeans

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


# -----------------------------
# FETCH EMBEDDINGS
# -----------------------------
def fetch_embeddings():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem,problem_embedding"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    data = r.json()

    print("Fetched rows:", len(data))

    return data


# -----------------------------
# PARSE VECTOR
# -----------------------------
def parse_vector(v):

    if v is None:
        return None

    if isinstance(v, list):
        return v

    v = v.strip("[]")

    return [float(x) for x in v.split(",")]


# -----------------------------
# UPDATE CLUSTER RESULT
# -----------------------------
def update_cluster(row_id, cluster_id, size):

    payload = {
        "cluster_id": int(cluster_id),
        "cluster_size": int(size)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Updated:", row_id, "cluster", cluster_id)
    else:
        print("Update failed:", r.text)


# -----------------------------
# MAIN CLUSTERING
# -----------------------------
def main():

    rows = fetch_embeddings()

    if not rows:
        print("No data found")
        return

    vectors = []
    ids = []

    for r in rows:

        vec = parse_vector(r["problem_embedding"])

        if not vec:
            continue

        vectors.append(vec)
        ids.append(r["id"])

    if len(vectors) == 0:
        print("No embeddings available")
        return

    X = np.array(vectors)

    # -----------------------------
    # CLUSTER COUNT (√N rule)
    # -----------------------------
    n_clusters = max(3, int(math.sqrt(len(X))))

    print("Total ideas:", len(X))
    print("Using clusters:", n_clusters)

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(X)

    # -----------------------------
    # CALCULATE CLUSTER SIZE
    # -----------------------------
    cluster_sizes = {}

    for l in labels:
        cluster_sizes[l] = cluster_sizes.get(l, 0) + 1

    # -----------------------------
    # UPDATE DATABASE
    # -----------------------------
    for row_id, label in zip(ids, labels):

        size = cluster_sizes[label]

        update_cluster(row_id, label, size)

    print("Clustering complete")


if __name__ == "__main__":
    main()
