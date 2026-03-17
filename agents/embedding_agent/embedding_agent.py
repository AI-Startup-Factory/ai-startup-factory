import os
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.database import db

# Load model (384-dimension)
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_unembedded_ideas():
    """
    Mengambil data yang embedding-nya masih kosong.
    """
    # Tambahkan filter is_duplicate=eq.false agar tidak memproses ulang duplikat
    query = "problem_embedding=is.null&select=id,problem&limit=25"
    return db.fetch_records("ideas", query)

def update_embedding(idea_id, embedding_vector):
    """
    Update vektor ke database.
    """
    # Pastikan formatnya adalah list untuk dikonversi ke pgvector oleh Supabase
    payload = {
        "problem_embedding": embedding_vector.tolist(),
        # Opsional: Jika Anda punya kolom status, update di sini
        # "embedding_status": "completed" 
    }
    return db.update_record("ideas", idea_id, payload)

def main():
    print("=== AI Startup Factory: Embedding Agent ===")
    
    ideas = fetch_unembedded_ideas()
    
    if not ideas:
        print("✅ No pending ideas found for embedding.")
        return

    print(f"📡 Processing embeddings for {len(ideas)} records...")

    success_count = 0
    for item in ideas:
        text_to_embed = item.get("problem")
        idea_id = item.get("id")
        
        if not text_to_embed:
            continue

        try:
            # Generate vector
            embedding = model.encode(text_to_embed)
            
            if update_embedding(idea_id, embedding):
                print(f"✅ Embedded ID: {idea_id}")
                success_count += 1
            else:
                print(f"❌ DB update failed for ID: {idea_id}")
                
        except Exception as e:
            print(f"🔥 Error processing ID {idea_id}: {str(e)}")

    print(f"=== Embedding Task Completed: {success_count} records updated ===")

if __name__ == "__main__":
    main()
