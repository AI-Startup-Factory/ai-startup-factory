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
        sys.exit(1)


def load_trends():
    with open("data/trends.json") as f:
        return json.load(f)


def generate_startup_analysis(problem):

    url = "https://openrouter.ai/api/v1/chat/completions"

    prompt = f"""
You are a startup analyst.

Analyze the following problem and propose a startup idea.

Problem:
{problem}

Return ONLY JSON:

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

    try:
        return json.loads(content)
    except:
        print("JSON parse error:", content)
        return None


def save_to_supabase(problem, analysis):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    payload = {
        "problem": problem,
        "solution": analysis["solution"],
        "market": analysis["market"],
        "audience": analysis["audience"],
        "revenue_model": analysis["revenue_model"],
        "moat": analysis["moat"],
        "score": analysis["score"]
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("Inserted:", problem)
    print("Status:", r.status_code)

    if r.text:
        print("Response:", r.text)


def main():

    check_env()

    trends = load_trends()

    for t in trends[:5]:

        problem = t.get("title")

        print("Analyzing:", problem)

        analysis = generate_startup_analysis(problem)

        if analysis:
            save_to_supabase(problem, analysis)


if __name__ == "__main__":
    main()
