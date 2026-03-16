import json
import re
import random
import time
import requests
from core.config import settings
from core.database import db

def load_signals():
    """Retrieves unprocessed signals from the database."""
    # Pastikan MAX_IDEAS_PER_RUN ada di core/config.py
    limit = getattr(settings, "MAX_IDEAS_PER_RUN", 50)
    query = f"processed=eq.false&select=id,title&limit={limit * 2}"
    return db.fetch_records("signals", query)

def mark_signal_processed(signal_id):
    """Marks a signal as processed using centralized DB wrapper."""
    return db.update_record("signals", signal_id, {"processed": True})

def save_ideas_to_db(ideas_data, signal_ids):
    """Persists generated ideas using centralized DB wrapper."""
    success_count = 0
    
    for item in ideas_data:
        # Menyesuaikan dengan skema tabel 'ideas' di database Anda
        payload = {
            "problem": item.get("problem"),
            "solution": item.get("solution"),
            "audience": item.get("audience", "General Target"),
            "market": item.get("market") # Pastikan kolom ini ada, atau ganti ke 'market_size'
        }
        
        # MENGGUNAKAN WRAPPER DATABASE YANG BARU
        if db.insert_record("ideas", payload):
            success_count += 1
        else:
            print(f"❌ Failed to insert idea: {item.get('problem')[:30]}...")

    # Jika ada yang berhasil, tandai signal asal sebagai 'sudah diproses'
    if success_count > 0:
        for sid in signal_ids:
            mark_signal_processed(sid)
    
    return success_count

def discover_free_models():
    """Dynamically finds free models from OpenRouter."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if r.status_code == 200:
            models = r.json().get("data", [])
            return [m["id"] for m in models if ":free" in m["id"]]
    except:
        return []
    return []

def call_ai(prompt):
    """Robust AI call with model fallback."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory",
        "X-Title": "AI Startup Factory"
    }

    # Ambil list model dari config (MODELS) dan gabungkan dengan model gratis terbaru
    static_models = getattr(settings, "MODELS", ["google/gemini-2.0-flash-exp:free"])
    all_potential_models = list(set(static_models + discover_free_models()))
    random.shuffle(all_potential_models)

    for model in all_potential_models:
        print(f"🤖 Trying model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "response_format": {"type": "json_object"} 
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            print(f"⚠️ Model {model} returned status: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Connection error with {model}: {e}")
            continue
    return None

def main():
    print("\n🚀 AI Startup Factory: Idea Generation Pipeline")
    
    signals = load_signals()
    if not signals:
        print("ℹ️ No new signals to process. Ingestion might be empty.")
        return

    signal_titles = [s["title"] for s in signals]
    signal_ids = [s["id"] for s in signals]
    
    print(f"📡 Found {len(signal_titles)} signals. Consulting AI...")

    limit = getattr(settings, "MAX_IDEAS_PER_RUN", 50)
    prompt = f"""
    Based on these emerging tech signals: {json.dumps(signal_titles)}
    Generate a JSON list of exactly {limit} startup ideas.
    Each idea MUST focus on a specific, non-obvious problem.
    
    RETURN ONLY VALID JSON:
    {{
      "ideas": [
        {{
          "problem": "detailed description",
          "solution": "specific technical solution",
          "market": "category",
          "audience": "target user"
        }}
      ]
    }}
    """

    response = call_ai(prompt)
    if not response:
        print("❌ CRITICAL: All AI models failed or returned no response.")
        return

    try:
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        data = json.loads(clean_json)
        ideas_list = data.get("ideas", data) if isinstance(data, dict) else data

        if not isinstance(ideas_list, list):
            print("❌ AI returned invalid format (not a list).")
            return

        saved = save_ideas_to_db(ideas_list, signal_ids)
        print(f"✅ Pipeline finished. {saved} new ideas saved to database.")

    except Exception as e:
        print(f"❌ Failed to parse AI response: {e}\nResponse: {response[:100]}...")

if __name__ == "__main__":
    main()
