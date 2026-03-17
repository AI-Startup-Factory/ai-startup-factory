import math
import numpy as np
from sklearn.cluster import KMeans
from core.config import settings
from core.database import db
# Import utilitas proyeksi Anda
from agents.utils.vector_projection import project_vector 

def fetch_ideas_with_embeddings():
    query = "select=id,problem,problem_embedding&problem_embedding=is.not.null&cluster_id=is.null"
    return db.fetch_records("ideas", query)

def update_cluster_metadata(row_id, cluster_id, size):
    payload = {
        "cluster_id": int(cluster_id),
        "cluster_size": int(size)
    }
    return db.update_record("ideas", row_id, payload)

def main():
    print("=== AI Startup Factory: Semantic Clusterer ===")
    
    rows = fetch_ideas_with_embeddings()
    
    if not rows:
        print("✅ No new ideas found with valid embeddings. Everything is already clustered.")
        return

    vectors = []
    ids = []

    print(f"📡 Processing {len(rows)} potential records...")

    for r in rows:
        vec = r.get("problem_embedding")
        
        if vec:
            # Gunakan utilitas proyeksi Anda untuk memastikan dimensi ALWAYS 384
            # Ini akan menangani dimensi 1536, 1024, dll secara otomatis
            projected_vec = project_vector(vec)
            
            if projected_vec and len(projected_vec) == 384:
                vectors.append(projected_vec)
                ids.append(r["id"])

    if not vectors:
        print("❌ No usable embedding vectors found after projection check.")
        return

    X = np.array(vectors)
    total_samples = len(X)

    # KMeans butuh n_samples >= n_clusters
    # Kita buat n_clusters dinamis namun aman
    if total_samples < 2:
        print(f"ℹ️ Only {total_samples} sample(s). Assigning to default cluster 0...")
        for row_id in ids:
            update_cluster_metadata(row_id, 0, 1)
        return

    n_clusters = max(1, min(int(math.sqrt(total_samples)), total_samples))
    
    print(f"🤖 Clustering {total_samples} ideas into {n_clusters} groups...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    cluster_sizes = {}
    for label in labels:
        cluster_sizes[label] = cluster_sizes.get(label, 0) + 1

    print(f"💾 Syncing to Supabase...")
    success_count = 0
    for row_id, label in zip(ids, labels):
        if update_cluster_metadata(row_id, label, cluster_sizes[label]):
            success_count += 1

    print(f"✅ Success: {success_count}/{total_samples} ideas clustered.")

if __name__ == "__main__":
    main()
