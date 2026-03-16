import json
import re
import time
import random
# Import core infrastructure
from core.config import settings
from core.database import db
import requests

def clean_int_score(val):
    """Safely converts any AI output value into a valid Integer for DB."""
    try:
        if val is None: return 0
        # Convert to float first (to handle "8.5"), then round and int
        return int(round(float(val)))
    except (ValueError, TypeError):
        return 0

def fetch_unscored_ideas():
    """Retrieves ideas that are missing the final opportunity_score."""
    query = "opportunity_score=is.null&select=id,problem&limit=25"
    return db.fetch_records("ideas", query)

def call_scoring_ai(problem):
    """Calls AI to evaluate the startup idea using centralized model list."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    prompt = f"""
    You are a venture capital analyst. Evaluate this startup opportunity.
    Problem: {problem}
    
    Score each category from 0 to 10.
    Return STRICT JSON format:
    {{
      "trend": number,
      "market": number,
      "competition": number,
      "feasibility": number,
      "founder_fit": number
    }}
    """

    # Robust model rotation from core
    all_models = settings.MODELS.copy()
    random.shuffle(all_models)

    for model in all_models:
        print(f"🔬 Scoring with model: {model}")
        try:
            r = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }, timeout=60)
            
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                # Clean potential markdown
                clean_json = re.sub(r"```json\s?|\s?```", "", content).strip()
                return json.loads(clean_json)
            elif r.status_code == 429:
                continue
        except:
            continue
    return None

def calculate_weighted_final(scores):
    """Calculates final score (0-100) based on weighted categories."""
    t = clean_int_score(scores.get("trend"))
    m = clean_int_score(scores.get("market"))
    c = clean_int_score(scores.get("competition"))
    f = clean_int_score(scores.get("feasibility"))
    ff = clean_int_score(scores.get("founder_fit"))

    # Weighted calculation (Result 0-10)
    weighted_sum = (
        0.30 * t +
        0.25 * m +
        0.20 * c +
        0.15 * f +
        0.10 * ff
    )
    # Return as integer (scale 0-100)
    return int(round(weighted_sum * 10))

def update_idea_scores(row_id, scores, final_score):
    """Persists detailed scores and final rank to database."""
    payload = {
        "trend_score": clean_int_score(scores.get("trend")),
        "market_score": clean_int_score(scores.get("market")),
        "competition_score": clean_int_score(scores.get("competition")),
        "feasibility_score": clean_int_score(scores.get("feasibility")),
        "founder_fit_score": clean_int_score(scores.get("founder_fit")),
        "opportunity_score": final_score
    }
    return db.update_record("ideas", row_id, payload)

def main():
    print("=== AI Startup Factory: Opportunity Scorer ===")
    
    ideas = fetch_unscored_ideas()
    if not ideas:
        print("✅ No new ideas found for scoring.")
        return

    print(f"📡 Processing {len(ideas)} ideas...")

    for row in ideas:
        problem = row["problem"]
        idea_id = row["id"]
        print(f"\n📝 Analyzing: {problem[:60]}...")

        scores_data = call_scoring_ai(problem)
        if not scores_data:
            print(f"❌ AI scoring failed for ID: {idea_id}")
            continue

        final_score = calculate_weighted_final(scores_data)
        
        if update_idea_scores(idea_id, scores_data, final_score):
            print(f"✅ Success: ID {idea_id} scored {final_score}/100")
        else:
            print(f"❌ DB Update failed for ID: {idea_id}")
        
        time.sleep(1) # Safety delay

    print("\n=== Scoring Session Completed ===")

if __name__ == "__main__":
    main()
