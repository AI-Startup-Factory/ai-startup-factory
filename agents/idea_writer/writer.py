import time
import json
import re
import random
# Import core infrastructure
from core.config import settings
from core.database import db
import requests

def fetch_signals():
    """Retrieves unprocessed signals from the database using core wrapper."""
    query = f"processed=eq.false&limit={settings.MAX_IDEAS_PER_RUN}"
    return db.fetch_records("signals", query)

def insert_idea(data):
    """Persists detailed idea analysis to the ideas table."""
    # We use a direct post to ideas table
    url = f"{settings.SUPABASE_URL}/rest/v1/ideas"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url, headers=headers, json=data)
        return r.status_code in [200, 201, 204]
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return False

def mark_processed(signal_id):
    """Updates signal status after successful processing."""
    return db.update_record("signals", signal_id, {"processed": True})

def call_llm(prompt):
    """Calls LLM with fallback mechanism using settings.MODELS."""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory",
        "X-Title": "AI Startup Factory - Writer Agent"
    }

    # Use the robust model list from core
    all_models = settings.MODELS.copy()
    random.shuffle(all_models)

    for model in all_models:
        print(f"✍️ Attempting analysis with model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }

        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                print(f"⚠️ Rate limit for {model}. Trying next...")
                continue
        except:
            continue
    
    return None

def build_prompt(title, content):
    """Constructs the analytical prompt for the AI."""
    return f"""
    You are a startup founder and market analyst. Analyze this signal and extract a startup opportunity.
    Return STRICT JSON ONLY.

    Signal Title: {title}
    Signal Content: {content}

    JSON Structure:
    {{
      "problem": "detailed problem",
      "solution": "detailed technical solution",
      "market": "category",
      "audience": "who is this for",
      "revenue_model": "how to make money",
      "moat": "competitive advantage",
      "market_size": "TAM/SAM estimate",
      "competition": "existing players or alternatives"
    }}
    """

def clean_and_parse(text):
    """Robust JSON parsing with markdown removal."""
    try:
        cleaned = re.sub(r"```json\s?|\s?```", "", text).strip()
        return json.loads(cleaned)
    except:
        return None

def main():
    print("=== AI Startup Factory: Idea Writer Agent ===")
    
    signals = fetch_signals()
    if not signals:
        print("✅ No new signals to analyze.")
        return

    print(f"📡 Processing {len(signals)} signals...")

    processed_count = 0
    for s in signals:
        signal_id = s["id"]
        title = s["title"]
        content = s.get("content", "No content provided.")

        print(f"\n📝 Analyzing Signal: {title[:50]}...")
        prompt = build_prompt(title, content)
        response = call_llm(prompt)

        if not response:
            print(f"❌ Failed to get analysis for Signal {signal_id}")
            continue

        parsed = clean_and_parse(response)
        if not parsed:
            print(f"❌ Failed to parse JSON for Signal {signal_id}")
            continue

        # Map parsed data to database schema
        idea_data = {
            "problem": parsed.get("problem"),
            "solution": parsed.get("solution"),
            "market": parsed.get("market"),
            "audience": parsed.get("audience"),
            "revenue_model": parsed.get("revenue_model"),
            "moat": parsed.get("moat"),
            "market_size": parsed.get("market_size"),
            "competition": parsed.get("competition")
        }

        if insert_idea(idea_data):
            mark_processed(signal_id)
            processed_count += 1
            print(f"✅ Idea successfully written and saved.")
        
        # Respect API limits
        time.sleep(1)

    print(f"\n=== Task Completed: {processed_count} ideas generated ===")

if __name__ == "__main__":
    main()
