import os
import json
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_LIST = [
"stepfun/step-3.5-flash:free",
"arcee-ai/trinity-large-preview:free",
"z-ai/glm-4.5-air:free",
"nvidia/nemotron-3-nano-30b-a3b:free"
]


# ===============================
# LOAD IDEAS
# ===============================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?trend_strength=is.null&select=*"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    return r.json()


# ===============================
# CALL AI (BATCH MODE)
# ===============================

def analyze_batch(ideas):

    url = "https://openrouter.ai/api/v1/chat/completions"

    problems = []

    for idea in ideas:
        problems.append(idea["problem"])

    prompt = f"""
Analyze the following startup problems.

Return JSON array.

Each item must contain:

problem
market_size
competition
trend_strength (1-10)
success_probability (1-10)

Problems:

{json.dumps(problems, indent=2)}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in MODEL_LIST:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages":[
                {"role":"user","content":prompt}
            ]
        }

        try:

            r = requests.post(url,headers=headers,json=payload,timeout=120)

            if r.status_code != 200:
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json","").replace("```","").strip()

            return json.loads(content)

        except Exception as e:

            print("Model failed:",model,e)

    return None


# ===============================
# UPDATE DATABASE
# ===============================

def update_idea(problem,analysis):

    url = f"{SUPABASE_URL}/rest/v1/ideas?problem=eq.{problem}"

    payload = {
        "market_size":analysis["market_size"],
        "competition":analysis["competition"],
        "trend_strength":analysis["trend_strength"],
        "success_probability":analysis["success_probability"]
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":"application/json"
    }

    r = requests.patch(url,json=payload,headers=headers)

    print("Updated:",problem,r.status_code)


# ===============================
# MAIN
# ===============================

def main():

    ideas = load_ideas()

    if not ideas:
        print("No ideas to analyze")
        return

    batch = ideas[:10]

    print("Analyzing batch of",len(batch),"ideas")

    analysis_results = analyze_batch(batch)

    if not analysis_results:
        print("AI failed")
        return

    for item in analysis_results:

        problem = item["problem"]

        update_idea(problem,item)


if __name__ == "__main__":
    main()
