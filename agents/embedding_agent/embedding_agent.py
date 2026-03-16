import os
from sentence_transformers import SentenceTransformer
# Import core infrastructure
from core.config import settings
from core.database import db

# Load model at module level to avoid re-loading for every function call
# Using all-MiniLM-L6-v2 (384-dimension) as per pgvector specifications
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_unembedded_ideas():
    """
    Retrieves ideas where 'problem_embedding' is null using the core database wrapper.
    """
    query = "problem_embedding=is.null&select=id,problem&limit=25"
    return db.fetch_records("ideas", query)

def update_embedding(idea_id, embedding_vector):
    """
    Updates the embedding vector in Supabase via the centralized database client.
    """
    payload = {
        "problem_embedding": embedding_vector.tolist()
    }
    return db.update_record("ideas", idea_id, payload)

def main():
    print("=== AI Startup Factory: Embedding Agent ===")
    
    # Fail-fast: Validate core configuration
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        print("❌ Critical Error: Missing Supabase credentials in settings.")
        return

    ideas = fetch_unembedded_ideas()
    
    if not ideas:
        print("✅ No pending ideas found for embedding.")
        return

    print(f"📡 Processing embeddings for {len(ideas)} records...")

    for item in ideas:
        text_to_embed = item.get("problem")
        idea_id = item.get("id")
        
        if not text_to_embed:
            print(f"⚠️ Skipping ID {idea_id}: Problem text is empty.")
            continue

        try:
            # Generate vector locally using sentence-transformers
            embedding = model.encode(text_to_embed)
            
            # Sync with Supabase
            if update_embedding(idea_id, embedding):
                print(f"✅ Successfully embedded ID: {idea_id}")
            else:
                print(f"❌ Database update failed for ID: {idea_id}")
                
        except Exception as e:
            print(f"🔥 Critical error processing ID {idea_id}: {str(e)}")

    print("=== Embedding Task Completed ===")

if __name__ == "__main__":
    main()
