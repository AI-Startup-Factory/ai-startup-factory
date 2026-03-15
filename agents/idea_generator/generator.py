import os
import requests
import re
import random
import time
from pathlib import Path

# Config & Env
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
# MODEL POOL (Large Fallback List)
# ================================
MODEL_LIST = [
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "arcee-ai/trinity-mini:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "openai/gpt-oss-20b:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "google/gemma-3-27b-it:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-4b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3n-e2b-it:free"
]

MAX_SIGNALS = 15
MAX_IDEAS = 10

# ================================
# LOAD SIGNALS
# ================================
def load_signals():
    # Mengambil sinyal yang belum diproses (processed = false)
    url = f"{SUPABASE_URL}/rest/v1/signals?processed=eq.false&select=id,title&limit={MAX_SIGNALS}"
    r = requests.get(url, headers=SUPABASE_HEADERS)
    if r.status_code != 200:
        print("Failed loading signals:", r.text)
        return []
    return r.json()

# ================================
# DISCOVER EXTRA FREE MODELS
# ================================
def discover_free_models():
    url = "https://openrouter.ai/api/v1/models"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return []
        models = r.json()["data"]
        discovered = [m["id"] for m in models if ":free" in m["id"] and m["id"] not in MODEL_LIST]
        return discovered
    except:
        return []

# ================================
# CALL AI (Robust Fallback System)
# ================================
def call_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory",
        "X-Title": "AI Startup Factory"
    }

    combined_models = MODEL_LIST.copy()
    random.shuffle(combined_models)
    
    # Tambahkan discovered models ke akhir antrean jika perlu
    extra = discover_free_models()
    random.shuffle(extra)
    all_models = combined_models + extra

    for model in all_models:
        print(f"Trying model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": {"type": "json_object"} # Memaksa output JSON
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                print(f"Rate limit hit for {model}, switching...")
                continue
        except:
            continue
    return None

# ================================
# SAVE IDEAS (Aligned with Schema)
# ================================
def save_ideas_to_db(ideas_data, signal_ids):
    url = f"{SUPABASE_URL}/rest/v1/ideas"
    
    for item in ideas_data:
        # Menyesuaikan dengan kolom problem dan solution (Bukan 'idea')
        payload = {
            "problem": item.get("problem"),
            "solution": item.get("solution"),
            "market": item.get("market"),
            "audience": item.get("audience", "General")
        }
        
        r = requests.post(url, headers=SUPABASE_HEADERS, json=payload)
        if r.status_code in [200, 201]:
            print(f"Saved: {payload['problem'][:50]}...")
        else:
            print(f"Insert failed: {r.text}")

    # Mark signals as processed
    for sid in signal_ids:
        patch_url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{sid}"
        requests.patch(patch_url, headers=SUPABASE_HEADERS, json={"processed": True})

# ================================
# MAIN PIPELINE
# ================================
def main():
    print("--- Starting Idea Generation Pipeline ---")
    
    signals = load_signals()
    if not signals:
        print("No unprocessed signals found.")
        return

    signal_titles = [s["title"] for s in signals]
    signal_ids = [s["id"] for s in signals]
    
    print(f"Loaded {len(signal_titles)} signals.")

    prompt = f"""
    Based on these technology signals:
    {json_titles if 'json_titles' in locals() else signal_titles}

    Act as a startup founder. Generate {MAX_IDEAS} unique startup concepts.
    Return ONLY a JSON array of objects with this structure:
    [
      {{
        "problem": "detailed problem description",
        "solution": "how technology solves it",
        "market": "industry name",
        "audience": "target users"
      }}
    ]
    """

    response = call_ai(prompt)
    if not response:
        print("Failed to generate ideas after trying all models.")
        return

    try:
        # Pembersihan teks jika AI memberikan markdown
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        ideas_data = json.loads(clean_json)
        
        if isinstance(ideas_data, dict) and "ideas" in ideas_data:
            ideas_data = ideas_data["ideas"]

        print(f"Generated {len(ideas_data)} ideas. Saving to database...")
        save_ideas_to_db(ideas_data, signal_ids)
        
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        print("Raw response:", response[:200])

if __name__ == "__main__":
    import json
    main()
