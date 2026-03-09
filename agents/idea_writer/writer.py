import os
import json
import requests
import sys

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "google/gemma-3-12b-it:free"


def check_env():
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_API_KEY:
        print("Missing environment variables")
        sys.exit(1)


def load_trends():
    with open("data/trends.json") as f:
        return json.load(f)


# ===============================
# CHECK IF IDEA EXISTS
# ===============================
def idea_exists(problem):

    url = f"{SUPABASE_URL}/rest/v1/ideas?problem=eq.{problem}&select=id"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return False

    data = r.json()

    return len(data) > 0


# ===============================
# BATCH AI CALL
# ===============================
def generate_batch_analysis(problems):

    url = "https://openrouter.ai/api/v1/chat/completions"

    joined = "\n".join([f"{i+1}. {p}" for i, p in enumerate(problems)])

    prompt = f"""
You are a startup analyst.

Analyze the following list of problems and propose startup opportunities.

Problems:
{joined}

Return ONLY valid JSON array.

Example format:

[
 {{
  "problem": "...",
  "solution": "...",
  "market": "...",
  "audience": "...",
  "revenue_model": "...",
  "moat": "...",
  "score": number
 }}
]
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

    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except Exception as e:
        print("JSON parse error:", e)
        print(content)
        return None


# ===============================
# INSERT INTO SUPABASE
# ===============================
def save_to_supabase(item):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    payload = {
        "problem": item.get("problem"),
        "solution": item.get("solution"),
        "market": item.get("market"),
        "audience": item.get("audience"),
        "revenue_model": item.get("revenue_model"),
        "moat": item.get("moat"),
        "score": int(float(item.get("score", 0)))
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code == 201:
        print("Inserted:", payload["problem"])
    else:
        print("Insert error:", r.status_code)
        print(r.text)


# ===============================
# MAIN
# ===============================
def main():

    check_env()

    trends = load_trends()

    problems = []

    for t in trends[:5]:

        problem = t.get("title")

        if not problem:
            continue

        if idea_exists(problem):
            print("Skipped (already exists):", problem)
            continue

        problems.append(problem)

    if len(problems) == 0:
        print("No new ideas to analyze")
        return

    print("Calling AI for", len(problems), "problems")

    results = generate_batch_analysis(problems)

    if not results:
        print("AI failed")
        return

    for item in results:

        save_to_supabase(item)


if __name__ == "__main__":
    main()
