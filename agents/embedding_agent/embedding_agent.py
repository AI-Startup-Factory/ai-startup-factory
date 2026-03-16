import os
import requests
import torch
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Load model (Prinsip 1: Modularization)
# Menggunakan model 384-dimension sesuai Super Context
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_unembedded_ideas():
    # Mengambil ide yang problem_embedding-nya masih kosong
    # Pastikan mengambil kolom 'problem' karena 'idea' sudah tidak ada
    url = f"{SUPABASE_URL}/rest/v1/ideas?problem_embedding=is.null&select=id,problem&limit=25"
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else []

def update_embedding(idea_id, embedding_vector):
    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"
    payload = {
        "problem_embedding": embedding_vector.tolist()
    }
    r = requests.patch(url, headers=headers, json=payload)
    return r.status_code in [200, 204]

def main():
    print("=== Running Embedding Agent ===")
    ideas = fetch_unembedded_ideas()
    
    if not ideas:
        print("No ideas need embedding.")
        return

    print(f"Generating embeddings for {len(ideas)} ideas...")

    for item in ideas:
        text_to_embed = item.get("problem")
        if not text_to_embed:
            continue

        try:
            # Generate vector
            embedding = model.encode(text_to_embed)
            
            # Push to Supabase
            success = update_embedding(item["id"], embedding)
            if success:
                print(f"Successfully embedded ID: {item['id']}")
            else:
                print(f"Failed to update embedding for ID: {item['id']}")
        except Exception as e:
            print(f"Error processing ID {item['id']}: {e}")

if __name__ == "__main__":
    main()
