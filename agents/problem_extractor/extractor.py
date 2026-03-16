import json
import re
import time
import random
import requests
# Import core infrastructure
from core.config import settings
from core.database import db

def fetch_pending_extractions():
    """
    Retrieves ideas from the 'ideas' table where 'solution' is missing,
    using 'problem' as the source for enrichment.
    """
    query = f"solution=is.null&select=id,problem&limit={settings.MAX_IDEAS_PER_RUN}"
    return db.fetch_records("ideas", query)

def update_extracted_data(idea_id, data):
    """
    Persists enriched business details back to the 'ideas' table.
    """
    payload = {
        "problem": data.get("problem"),
        "solution": data.get("solution"),
        "audience": data.get("audience"),
        "market": data.get("market", "General")
    }
    return db.update_record("ideas", idea_id, payload)

def call_extraction_ai(raw_text):
    """
    Uses AI to transform raw problem descriptions into structured 
    business entities with fallback model support.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    prompt = f"""
    Act as a business analyst. Analyze this startup idea and extract structured details.
    Raw Input: {raw_text}

    Return ONLY a JSON object with this exact structure:
    {{
        "problem": "detailed problem statement",
        "solution": "detailed solution description",
        "audience": "target user persona",
        "market": "industry category"
    }}
    """

    all_models = settings.MODELS.copy()
    random.shuffle(all_models)

    for model in all_models:
        print(f"🧩 Problem Extractor using: {model}")
        try:
            r = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }, timeout=60)

            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                clean_json = re.sub(r"```json\s?|\s?```", "", content).strip()
                return json.loads(clean_json)
        except:
            continue
        
    return None

def main():
    print("=== AI Startup Factory: Problem Extractor Agent ===")
    
    tasks = fetch_pending_extractions()
    if not tasks:
        print("✅ No pending extraction tasks found.")
        return

    print(f"📡 Refining {len(tasks)} raw problem entries...")

    success_count = 0
    for item in tasks:
        raw_text = item.get("problem")
        idea_id = item.get("id")

        if not raw_text: continue

        print(f"🔍 Extracting details for ID: {idea_id}...")
        enriched_data = call_extraction_ai(raw_text)

        if enriched_data:
            if update_extracted_data(idea_id, enriched_data):
                print(f"✅ Successfully structured ID: {idea_id}")
                success_count += 1
        
        time.sleep(1)

    print(f"\n=== Task Completed: {success_count}/{len(tasks)} records enriched ===")

if __name__ == "__main__":
    main()
