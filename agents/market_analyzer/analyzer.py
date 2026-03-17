import json
import re
import time
import requests
from core.config import settings
from core.database import db

def load_pending_ideas():
    """Mengambil ide yang belum dianalisis (trend_strength is null)."""
    # Pastikan mengambil ID dan Problem
    query = "trend_strength=is.null&select=id,problem&limit=10"
    return db.fetch_records("ideas", query)

def update_idea_analysis(idea_id, analysis):
    """Menyimpan hasil analisis ke Supabase."""
    payload = {
        "market_size": analysis.get("market_size"),
        "competition": analysis.get("competition"),
        "trend_strength": analysis.get("trend_strength"),
        "success_probability": analysis.get("success_probability")
    }
    return db.update_record("ideas", idea_id, payload)

def discover_extra_models():
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            return [m["id"] for m in data if ":free" in m["id"]]
    except:
        return []
    return []

def call_market_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    # Ambil MODELS dari config, fallback ke list manual jika belum diupdate
    static_models = getattr(settings, "MODELS", ["google/gemini-2.0-flash-exp:free"])
    potential_models = list(set(static_models + discover_extra_models()))
    
    for model in potential_models:
        print(f"🔬 Analyzing market with model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                clean_content = re.sub(r"```json\s?|\s?```", "", content).strip()
                data = json.loads(clean_content)
                # Ambil list 'analysis'
                return data.get("analysis", data)
            elif r.status_code == 429:
                print(f"⚠️ Rate limit for {model}. Skipping...")
        except Exception as e:
            print(f"❌ Connection error with {model}: {e}")
        
        time.sleep(1)
    return None

def main():
    print("=== AI Startup Factory: Market & Trend Analyzer ===")
    
    ideas = load_pending_ideas()
    if not ideas:
        print("✅ No pending ideas for analysis.")
        return

    print(f"📡 Analyzing batch of {len(ideas)} ideas...")
    
    # PERBAIKAN: Kirim ID ke AI agar mapping 100% akurat
    analysis_input = [{"id": i["id"], "problem": i["problem"]} for i in ideas]
    
    prompt = f"""
    Analyze the following startup problems for market viability.
    Return ONLY a JSON object with a key "analysis" containing an array of objects.

    Each object must have:
    - id (MUST match the provided ID exactly)
    - market_size (brief description)
    - competition (brief description)
    - trend_strength (integer 1-10)
    - success_probability (integer 1-10)

    Data to analyze:
    {json.dumps(analysis_input, indent=2)}
    """

    results = call_market_ai(prompt)
    if not results:
        print("❌ Market analysis failed for this batch.")
        return

    success_updates = 0
    if isinstance(results, list):
        for item in results:
            idea_id = item.get("id")
            if idea_id:
                if update_idea_analysis(idea_id, item):
                    success_updates += 1
                    print(f"✅ Saved analysis for ID: {idea_id}")
                else:
                    print(f"⚠️ Failed to update DB for ID: {idea_id}")

    print(f"=== Analysis Completed: {success_updates}/{len(ideas)} updated ===")

if __name__ == "__main__":
    main()
