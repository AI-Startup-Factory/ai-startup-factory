import os
import requests
import json
import random

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "meta-llama/llama-3.3-70b-instruct:free"


# =========================
# FETCH IDEAS
# =========================

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem,cluster_id&opportunity_score=is.null&limit=30"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# =========================
# CALL AI
# =========================

def call_ai(prompt):

    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:

        r = requests.post(OPENROUTER_URL, headers=headers_ai, json=payload, timeout=90)

        if r.status_code != 200:
            print("AI error:", r.text)
            return None

        data = r.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI exception:", e)
        return None


# =========================
# SCORE IDEA
# =========================

def score_problem(problem):

    prompt = f"""
You are a venture capital analyst.

Evaluate this startup opportunity.

Problem:
{problem}

Score the following from 0 to 10:

Trend momentum
Market size
Competition density (reverse score: less competition = higher score)
Execution feasibility
Founder advantage potential

Return JSON format:

{{
"trend": number,
"market": number,
"competition": number,
"feasibility": number,
"founder_fit": number
}}
"""

    response = call_ai(prompt)

    if not response:
        return None

    try:
        data = json.loads(response)
        return data
    except:
        print("JSON parse failed:", response)
        return None


# =========================
# CALCULATE FINAL SCORE
# =========================

def calculate_score(scores):

    trend = scores["trend"]
    market = scores["market"]
    competition = scores["competition"]
    feasibility = scores["feasibility"]
    founder = scores["founder_fit"]

    final = (
        0.30 * trend +
        0.25 * market +
        0.20 * competition +
        0.15 * feasibility +
        0.10 * founder
    )

    return round(final * 10, 2)


# =========================
# UPDATE DATABASE
# =========================

def update_row(row_id, scores, final):

    payload = {
        "trend_score": scores["trend"],
        "market_score": scores["market"],
        "competition_score": scores["competition"],
        "feasibility_score": scores["feasibility"],
        "founder_fit_score": scores["founder_fit"],
        "opportunity_score": final
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200,204]:
        print("Updated score:", row_id)
    else:
        print("Update error:", r.text)


# =========================
# MAIN
# =========================

def main():

    rows = fetch_ideas()

    if not rows:
        print("No ideas to score")
        return

    for row in rows:

        problem = row["problem"]

        print("\nScoring:", problem)

        scores = score_problem(problem)

        if not scores:
            continue

        final = calculate_score(scores)

        update_row(row["id"], scores, final)


if __name__ == "__main__":
    main()
