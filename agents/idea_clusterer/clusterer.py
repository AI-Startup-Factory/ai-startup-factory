import math
import numpy as np
from sklearn.cluster import KMeans
from core.config import settings
from core.database import db

def fetch_ideas_with_embeddings():
    """
    Fetches all ideas that have embeddings for clustering process.
    """
    query = "select=id,problem,problem_embedding&problem_embedding=not.is.null"
    return db.fetch_records("ideas", query)

def update_cluster_metadata(row_id, cluster_id, size):
    """
    Persists the cluster assignment and cluster size to the database.
    """
    payload = {
        "cluster_id": int(cluster_id),
        "cluster_size": int(size)
    }
    return db.update_record("ideas", row_id, payload)

def main():
    print("=== AI Startup Factory: Semantic Clusterer ===")
    
    # 1. Data Acquisition
    rows = fetch_ideas_with_embeddings()
    
    if not rows:
        print("❌ No data found with valid embeddings. Run the Embedding Agent first.")
        return

    vectors = []
    ids = []

    # 2. Vector Preparation
    for r in rows:
        # Core database already returns list for JSONB columns, so no manual parsing needed
        vec = r.get("problem_embedding")
        if vec and isinstance(vec, list):
            vectors.append(vec)
            ids.append(r["id"])

    if not vectors:
        print("❌ No usable embedding vectors available.")
        return

    X = np.array(vectors)
    total_samples = len(X)

    # 3. Dynamic Cluster Count Determination (Rule of Thumb: √N)
    # We ensure a minimum of 3 clusters for meaningful grouping
    n_clusters = max(3, int(math.sqrt(total_samples)))

    print(f"📡 Total Ideas to Cluster: {total_samples}")
    print(f"🤖 Initializing KMeans with {n_clusters} clusters...")

    # 4. KMeans Execution
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )
    
    labels = kmeans.fit_predict(X)

    # 5. Calculate Frequency (Cluster Size)
    # This helps identify the most "crowded" or trending opportunity areas
    cluster_sizes = {}
    for label in labels:
        cluster_sizes[label] = cluster_sizes.get(label, 0) + 1

    # 6. Database Synchronization
    print(f"💾 Syncing cluster metadata to Supabase...")
    success_count = 0
    
    for row_id, label in zip(ids, labels):
        size = cluster_sizes[label]
        if update_cluster_metadata(row_id, label, size):
            success_count += 1
        else:
            print(f"⚠️ Failed to update record ID: {row_id}")

    records = db.fetch_records("ideas", "select=*&limit=5")
            print(f"DEBUG: First record keys: {records[0].keys() if records else 'Empty'}")


    print(f"✅ Clustering complete. {success_count}/{total_samples} records updated.")

if __name__ == "__main__":
    main()
