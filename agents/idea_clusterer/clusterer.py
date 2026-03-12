import os
import requests
import numpy as np
from sklearn.cluster import KMeans

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def fetch_embeddings():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem_embedding"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


def parse_vector(v):

    if isinstance(v, list):
        return v

    v = v.strip("[]")
    return [float(x) for x in v.split(",")]


def update_cluster(row_id, cluster_id, size):

    payload = {
        "cluster_id": int(cluster_id),
        "cluster_size": int(size)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code not in [200, 204]:
        print("Update failed:", r.text)


def main():

    rows = fetch_embeddings()

    if not rows:
        print("No embeddings found")
        return

    vectors = []
    ids = []

    for r in rows:

        if not r["problem_embedding"]:
            continue

        vec = parse_vector(r["problem_embedding"])

        vectors.append(vec)
        ids.append(r["id"])

    X = np.array(vectors)

    n_clusters = max(2, int(len(X) / 10))

    print("Clustering into", n_clusters, "clusters")

    model = KMeans(n_clusters=n_clusters, random_state=42)

    labels = model.fit_predict(X)

    cluster_sizes = {}

    for l in labels:
        cluster_sizes[l] = cluster_sizes.get(l, 0) + 1

    for row_id, label in zip(ids, labels):

        update_cluster(row_id, label, cluster_sizes[label])

    print("Clustering complete")


if __name__ == "__main__":
    main()
