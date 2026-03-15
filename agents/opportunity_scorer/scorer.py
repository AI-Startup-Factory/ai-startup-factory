import os
import requests
import json
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ===================================
# FALLBACK MODEL LIST
# ===================================

MODEL_LIST = [

"meta-llama/llama-3.3-70b-instruct:free",
"openai/gpt-oss-120b:free",
"google/gemma-3-27b-it:free",
"mistralai/mistral-small-3.1-24b-instruct:free",
"arcee-ai/trinity-large-preview:free",
"arcee-ai/trinity-mini:free",
"z-ai/glm-4.5-air:free",
"nvidia/nemotron-3-nano-30b-a3b:free",
"qwen/qwen3-next-80b-a3b-instruct:free",
"qwen/qwen3-coder:free",
"openai/gpt-oss-20b:free",
"nousresearch/hermes-3-llama-3.1-405b:free",
"google/gemma-3-12b-it:free",
"google/gemma-3-4b-it:free",
"google/gemma-3n-e4b-it:free",
"google/gemma-3n-e2b-it:free",
"meta-llama/llama-3.2-3b-instruct:free",
"qwen/qwen3-4b:free",
"liquid/lfm-2.5-1.2b-instruct:free",
"liquid/lfm-2.5-1.2b-thinking:free"
]


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ===================================
# FETCH IDEAS
# ===================================

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&opportunity_score=is.null&limit=25"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# ===================================
# DISCOVER EXTRA FREE MODELS
# ===================================

def discover_free_models():

    try:

        url = "https://openrouter.ai/api/v1/models"

        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            return []

        models = r.json()["data"]

        discovered = []

        for m in models:

            model_id = m["id"]

            if ":free" in model_id and model_id not in MODEL_LIST:

                discovered.append(model_id)

        return discovered

    except:

        return []


# ===================================
# CALL AI WITH FALLBACK
# ===================================

def call_ai(prompt):

    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Try primary models
    for model in MODEL_LIST:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:

            r = requests.post(
                OPENROUTER_URL,
                headers=headers_ai,
                json=payload,
                timeout=120
            )

            if r.status_code != 200:
                continue

            data = r.json()

            return data["choices"][0]["message"]["content"]

        except:
            continue

    # Discover additional models
    print("Discovering additional free models")

    extra_models = discover_free_models()

    for model in extra_models:

        print("Trying discovered model:", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:

            r = requests.post(
                OPENROUTER_URL,
                headers=headers_ai,
                json=payload,
                timeout=120
            )

            if r.status_code != 200:
                continue

            data = r.json()

            return data["choices"][0]["message"]["content"]

        except:
            continue

    print("All models failed")

    return None


# ===================================
# SCORE PROBLEM
# ===================================

def score_problem(problem):

    prompt = f"""
You are a venture capital analyst.

Evaluate this startup opportunity.

Problem:
{problem}

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

    response = call_ai(prompt)

    if not response:
        return None

    try:

        data = json.loads(response)

        return data

    except:

        print("JSON parse error:", response)

        return None


# ===================================
# CALCULATE FINAL SCORE
# ===================================

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


# ===================================
# UPDATE DATABASE
# ===================================

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

    if r.status_code in [200, 204]:

        print("Updated score:", row_id)

    else:

        print("Update failed:", r.text)


# ===================================
# MAIN
# ===================================

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

        time.sleep(2)


if __name__ == "__main__":

    main()
