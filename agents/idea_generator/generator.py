import json
import re
import random
import time
# Import infrastruktur core
from core.config import settings
from core.database import db
import requests # Tetap dibutuhkan untuk discovery model baru di OpenRouter

def load_signals():
    """Retrieves unprocessed signals from the database."""
    query = f"processed=eq.false&select=id,title&limit={settings.MAX_IDEAS_PER_RUN * 2}"
    return db.fetch_records("signals", query)

def mark_signal_processed(signal_id):
    """Marks a signal as processed to avoid duplicates in the next run."""
    return db.update_record("signals", signal_id, {"processed": True})

def save_ideas_to_db(ideas_data, signal_ids):
    """Persists generated ideas and marks their source signals as processed."""
    success_count = 0
    
    for item in ideas_data:
        payload = {
            "problem": item.get("problem"),
            "solution": item.get("solution"),
            "market": item.get("market"),
            "audience": item.get("audience", "General Target")
        }
        
        # Using database wrapper for insertion
        # Note: we use a simple POST here, for production we might add a 'create_record' to core.database
        url = f"{settings.SUPABASE_URL}/rest/v1/ideas"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code in [200, 201, 204]:
                success_count += 1
        except Exception as e:
            print(f"❌ Error saving idea to DB: {e}")

    if success_count > 0:
        for sid in signal_ids:
            mark_signal_processed(sid)
    
    return success_count

def discover_free_models():
    """Discovers new free models dynamically from OpenRouter if static list fails."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if r.status_code == 200:
            models = r.json().get("data", [])
            return [m["id"] for m in models if ":free" in m["id"]]
    except:
        return []
    return []

def call_ai(prompt):
    """Calls AI models with a robust fallback mechanism using the centralized model list."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory",
        "X-Title": "AI Startup Factory"
    }

    # Combine static models from core with dynamic ones
    all_potential_models = list(set(settings.MODELS + discover_free_models()))
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
            elif r.status_code == 429:
                print(f"⚠️ Rate limit for {model}. Switching...")
                continue
        except:
            continue
    return None

def main():
    print("\n🚀 AI Startup Factory: Idea Generation Pipeline")
    
    signals = load_signals()
    if not signals:
        print("✅ No new signals to process.")
        return

    signal_titles = [s["title"] for s in signals]
    signal_ids = [s["id"] for s in signals]
    
    print(f"📡 Processing {len(signal_titles)} signals to generate ideas...")

    prompt = f"""
    Based on these emerging tech signals: {json.dumps(signal_titles)}
    Generate a JSON list of {settings.MAX_IDEAS_PER_RUN} startup ideas.
    Each idea MUST focus on a specific, non-obvious problem.
    
    RETURN ONLY JSON:
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
        print("❌ CRITICAL: All AI models failed.")
        return

    try:
        # Clean potential markdown wrapping
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        data = json.loads(clean_json)
        ideas_list = data.get("ideas", data) if isinstance(data, dict) else data

        if not isinstance(ideas_list, list):
            print("❌ AI returned invalid format (not a list).")
            return

        saved = save_ideas_to_db(ideas_list, signal_ids)
        print(f"✅ Pipeline finished. {saved} new ideas born.")

    except Exception as e:
        print(f"❌ Failed to parse AI response: {e}")

if __name__ == "__main__":
    main()
