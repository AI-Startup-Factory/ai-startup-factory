import math
import numpy as np
from sklearn.cluster import KMeans
from core.config import settings
from core.database import db

def fetch_ideas_with_embeddings():
    """
    Mengambil ide yang sudah memiliki embedding tetapi belum dikelompokkan (cluster_id null).
    """
    # Menggunakan is.not.null untuk standar PostgREST
    query = "select=id,problem,problem_embedding&problem_embedding=is.not.null&cluster_id=is.null"
    return db.fetch_records("ideas", query)

def update_cluster_metadata(row_id, cluster_id, size):
    """
    Menyimpan hasil clustering ke database.
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
        print("✅ No new ideas found with valid embeddings. Everything is already clustered.")
        return

    vectors = []
    ids = []

    # 2. Vector Preparation
    for r in rows:
        vec = r.get("problem_embedding")
        if vec and isinstance(vec, list):
            # Pastikan dimensi sesuai (384 untuk all-MiniLM-L6-v2)
            if len(vec) == 384:
                vectors.append(vec)
                ids.append(r["id"])

    if not vectors:
        print("❌ No usable embedding vectors available (check dimension or nulls).")
        return

    X = np.array(vectors)
    total_samples = len(X)

    # 3. Dynamic Cluster Count Determination
    # Perbaikan: Pastikan n_clusters tidak lebih besar dari jumlah sampel
    n_clusters = max(1, min(int(math.sqrt(total_samples)), total_samples))
    
    if total_samples < 2:
        print(f"ℹ️ Too few samples ({total_samples}) for clustering. Skipping...")
        return

    print(f"📡 Total Ideas to Cluster: {total_samples}")
    print(f"🤖 Initializing KMeans with {n_clusters} clusters...")

    # 4. KMeans Execution
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )
    
    labels = kmeans.fit_predict(X)

    # 5. Calculate Frequency
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

    # PERBAIKAN: Indentasi disejajarkan dengan blok utama main()
    try:
        debug_check = db.fetch_records("ideas", "select=id,problem_embedding&limit=1")
        if debug_check:
            print(f"DEBUG: Data check successful. Keys found: {list(debug_check[0].keys())}")
    except Exception as e:
        print(f"DEBUG: Metadata check skipped: {e}")

    print(f"✅ Clustering complete. {success_count}/{total_samples} records updated.")

if __name__ == "__main__":
    main()
