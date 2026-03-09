import os
import json
import requests
import sys

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "z-ai/glm-4.5-air:free"


def check_env():
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_API_KEY:
        print("Missing environment variables")
        print("SUPABASE_URL:", bool(SUPABASE_URL))
        print("SUPABASE_KEY:", bool(SUPABASE_KEY))
        print("OPENROUTER_API_KEY:", bool(OPENROUTER_API_KEY))
        sys.exit(1)


def load_trends():
    try:
        with open("data/trends.json") as f:
            return json.load(f)
    except Exception as e:
        print("Failed loading trends:", e)
        sys.exit(1)


def generate_startup_analysis(problem):

    url = "https://openrouter.ai/api/v1/chat/completions"

    prompt = f"""
You are a startup analyst.

Analyze the following problem and propose a startup opportunity.

Problem:
{problem}

Return ONLY valid JSON:

{{
"solution": "...",
"market": "...",
"audience": "...",
"revenue_model": "...",
"moat": "...",
"score": number
}}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code != 200:
        print("AI ERROR:", r.text)
        return None

    content = r.json()["choices"][0]["message"]["content"]

    # Bersihkan markdown code block dari AI
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)
        return data
    except Exception as e:
        print("JSON parse error:", e)
        print("RAW AI RESPONSE:", content)
        return None


def save_to_supabase(problem, analysis):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    payload = {
        "problem": problem,
        "solution": analysis.get("solution"),
        "market": analysis.get("market"),
        "audience": analysis.get("audience"),
        "revenue_model": analysis.get("revenue_model"),
        "moat": analysis.get("moat"),
        "score": int(float(analysis.get("score", 0)))
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code == 201:
        print("Inserted:", problem)
    elif r.status_code == 409:
        print("Duplicate skipped:", problem)
    else:
        print("Insert error:", r.status_code)
        print("Response:", r.text)


def main():

    check_env()

    trends = load_trends()

    for t in trends[:5]:

        problem = t.get("title")

        if not problem:
            continue

        print("Analyzing:", problem)

        analysis = generate_startup_analysis(problem)

        if analysis:
            save_to_supabase(problem, analysis)
        else:
            print("Skipping due to AI error")


if __name__ == "__main__":
    main()
