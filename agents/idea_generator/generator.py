import os
import requests
import re
import random
import time
import json

# ================================
# CONFIGURATION & ENV
# ================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ================================
# MODEL POOL (Comprehensive Free List)
# ================================
MODEL_LIST = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "qwen/qwen3-4b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-mini:free",
    "z-ai/glm-4.5-air:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
]

MAX_SIGNALS = 15
MAX_IDEAS = 10

# ================================
# DATABASE TOOLS
# ================================

def load_signals():
    """Mengambil sinyal yang belum diolah."""
    url = f"{SUPABASE_URL}/rest/v1/signals?processed=eq.false&select=id,title&limit={MAX_SIGNALS}"
    try:
        r = requests.get(url, headers=SUPABASE_HEADERS)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def mark_signal_processed(signal_id):
    """Menandai sinyal agar tidak diolah ulang."""
    url = f"{SUPABASE_URL}/rest/v1/ideas" # Cek keberadaan ide terkait
    patch_url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{signal_id}"
    requests.patch(patch_url, headers=SUPABASE_HEADERS, json={"processed": True})

def save_ideas_to_db(ideas_data, signal_ids):
    """Menyimpan ide ke tabel ideas sesuai skema baru."""
    url = f"{SUPABASE_URL}/rest/v1/ideas"
    success_count = 0
    
    for item in ideas_data:
        payload = {
            "problem": item.get("problem"),
            "solution": item.get("solution"),
            "market": item.get("market"),
            "audience": item.get("audience", "General Target")
        }
        
        try:
            r = requests.post(url, headers=SUPABASE_HEADERS, json=payload)
            if r.status_code in [200, 201, 204]:
                success_count += 1
        except Exception as e:
            print(f"Error saving to DB: {e}")

    # Jika berhasil simpan ide, tandai sinyal asal sebagai 'processed'
    if success_count > 0:
        for sid in signal_ids:
            mark_signal_processed(sid)
    
    return success_count

# ================================
# AI ENGINE (With Robust Fallback)
# ================================

def discover_free_models():
    """Mencari model gratis baru jika list utama gagal semua."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models")
        if r.status_code == 200:
            models = r.json()["data"]
            return [m["id"] for m in models if ":free" in m["id"]]
    except:
        return []
    return []

def call_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory",
        "X-Title": "AI Startup Factory"
    }

    # Gabungkan list utama dengan penemuan baru, lalu acak
    all_potential_models = list(set(MODEL_LIST + discover_free_models()))
    random.shuffle(all_potential_models)

    for model in all_potential_models:
        print(f"Trying model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "response_format": {"type": "json_object"} 
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                if content: return content
            
            elif r.status_code == 429:
                print(f"Rate limit hit for {model}. Switching model...")
                continue
            else:
                print(f"Model {model} returned status {r.status_code}")
                continue
        except Exception as e:
            print(f"Connection error with {model}: {e}")
            continue

    return None

# ================================
# MAIN PIPELINE
# ================================

def main():
    print("\n--- Starting Idea Generation Pipeline ---")
    
    signals = load_signals()
    if not signals:
        print("No unprocessed signals found in database.")
        return

    signal_titles = [s["title"] for s in signals]
    signal_ids = [s["id"] for s in signals]
    
    print(f"Processing {len(signal_titles)} signals...")

    prompt = f"""
    Based on these emerging technology signals:
    {json.dumps(signal_titles)}

    Generate a JSON list of {MAX_IDEAS} startup ideas.
    Each idea MUST focus on a specific, non-obvious problem.
    
    REQUIRED JSON FORMAT (return ONLY this):
    {{
      "ideas": [
        {{
          "problem": "detailed specific problem description",
          "solution": "how technology solves it specifically",
          "market": "industry category",
          "audience": "who has this problem"
        }}
      ]
    }}
    """

    response = call_ai(prompt)
    if not response:
        print("CRITICAL: All AI models failed or returned empty results.")
        return

    try:
        # Robust Parsing: Bersihkan markdown jika ada
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        data = json.loads(clean_json)
        
        # Ambil list ide (handle jika AI membungkus dalam key 'ideas' atau langsung list)
        ideas_list = data.get("ideas", data) if isinstance(data, dict) else data

        if not isinstance(ideas_list, list):
            print("Error: AI did not return a list of ideas.")
            return

        print(f"Successfully generated {len(ideas_list)} ideas. Syncing to Supabase...")
        saved = save_ideas_to_db(ideas_list, signal_ids)
        print(f"Pipeline finished. {saved} ideas saved to database.")

    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        print("Raw AI Output was:", response[:300])

if __name__ == "__main__":
    main()
