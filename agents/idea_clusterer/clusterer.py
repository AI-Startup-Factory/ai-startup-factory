import math
import numpy as np
import json
from sklearn.cluster import KMeans
from core.config import settings
from core.database import db
from agents.utils.vector_projection import project_vector 

def fetch_ideas_with_embeddings():
    """
    Mengambil data dengan filter minimal untuk menghindari kegagalan filter URL.
    Validasi dilakukan secara manual di memori Python.
    """
    # Hanya filter cluster_id yang null
    query = "select=id,problem,problem_embedding&cluster_id=is.null"
    
    try:
        rows = db.fetch_records("ideas", query)
        if not rows:
            return []
            
        # Filter manual di Python untuk memastikan problem_embedding tersedia
        valid_rows = []
        for r in rows:
            emb = r.get("problem_embedding")
            if emb is not None:
                valid_rows.append(r)
        
        print(f"DEBUG: SQL found {len(rows)} records with null cluster_id.")
        print(f"DEBUG: {len(valid_rows)} of those have non-null embeddings.")
        return valid_rows
    except Exception as e:
        print(f"❌ Error fetching records: {e}")
        return []

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
        
        # Penanganan jika format dari DB adalah string (JSON-like)
        if isinstance(vec, str):
            try:
                vec = json.loads(vec)
            except:
                continue
        
        if vec:
            # Pastikan diproyeksikan ke target 384
            projected_vec = project_vector(vec)
            
            if projected_vec and len(projected_vec) == 384:
                vectors.append(projected_vec)
                ids.append(r["id"])

    if not vectors:
        print("❌ No usable embedding vectors found after dimension check.")
        return

    X = np.array(vectors)
    total_samples = len(X)

    # Handling jika ide terlalu sedikit untuk membentuk klaster KMeans murni
    if total_samples < 2:
        print(f"ℹ️ Only {total_samples} sample(s). Assigning to default cluster 0...")
        for row_id in ids:
            update_cluster_metadata(row_id, 0, 1)
        print("✅ Success: Assigned to default cluster.")
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
