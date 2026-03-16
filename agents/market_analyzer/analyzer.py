import json
import re
import time
import requests
# Import infrastruktur core
from core.config import settings
from core.database import db

def load_pending_ideas():
    """Retrieves ideas that haven't been analyzed for trend strength yet."""
    query = "trend_strength=is.null&select=id,problem&limit=10"
    return db.fetch_records("ideas", query)

def update_idea_analysis(idea_id, analysis):
    """Updates the idea with market analysis results."""
    payload = {
        "market_size": analysis.get("market_size"),
        "competition": analysis.get("competition"),
        "trend_strength": analysis.get("trend_strength"),
        "success_probability": analysis.get("success_probability")
    }
    return db.update_record("ideas", idea_id, payload)

def discover_extra_models():
    """Checks OpenRouter for any new free models not in our static list."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            return [m["id"] for m in data if ":free" in m["id"]]
    except:
        return []
    return []

def call_market_ai(prompt):
    """Executes AI analysis with robust fallback and JSON extraction."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    # Merging static core models with dynamic discovery
    potential_models = list(set(settings.MODELS + discover_extra_models()))
    
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
                # Cleaning and extraction
                clean_content = re.sub(r"```json\s?|\s?```", "", content).strip()
                data = json.loads(clean_content)
                
                # Handle both direct array or wrapped object
                return data.get("analysis", data) if isinstance(data, dict) else data
            
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
        print("✅ All ideas have been analyzed.")
        return

    print(f"📡 Analyzing batch of {len(ideas)} ideas...")
    
    problems_list = [i["problem"] for i in ideas]
    prompt = f"""
    Analyze the following startup problems for market viability.
    Return ONLY a JSON object with a key "analysis" containing an array of objects.

    Each object must have:
    - problem (original text)
    - market_size (description)
    - competition (description)
    - trend_strength (score 1-10)
    - success_probability (score 1-10)

    Problems to analyze:
    {json.dumps(problems_list, indent=2)}
    """

    results = call_market_ai(prompt)
    if not results:
        print("❌ Market analysis failed for this batch.")
        return

    # Create mapping for efficient updates
    problem_to_id = {i["problem"]: i["id"] for i in ideas}
    success_updates = 0

    if isinstance(results, list):
        for item in results:
            prob_text = item.get("problem")
            if prob_text in problem_to_id:
                idea_id = problem_to_id[prob_text]
                if update_idea_analysis(idea_id, item):
                    success_updates += 1
                    print(f"✅ Analysis saved for ID: {idea_id}")

    print(f"=== Analysis Completed: {success_updates}/{len(ideas)} updated ===")

if __name__ == "__main__":
    main()
