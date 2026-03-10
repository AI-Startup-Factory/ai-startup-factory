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


# ==============================
# LOAD IDEAS FROM SUPABASE
# ==============================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?market_size=is.null&select=*"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    return r.json()


# ==============================
# CALL AI
# ==============================

def analyze_market(problem, solution):

    url = "https://openrouter.ai/api/v1/chat/completions"

    prompt = f"""
Analyze this startup idea.

Problem:
{problem}

Solution:
{solution}

Return JSON:

{{
"market_size": "...",
"competition": "...",
"trend_strength": number 1-10,
"success_probability": number 1-10
}}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY},
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

            r = requests.post(url,headers=headers,json=payload,timeout=90)

            if r.status_code != 200:
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json","").replace("```","").strip()

            return json.loads(content)

        except:
            continue

    return None


# ==============================
# UPDATE DATABASE
# ==============================

def update_idea(id,analysis):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{id}"

    payload = {
        "market_size":analysis["market_size"],
        "competition":analysis["competition"],
        "trend_strength":analysis["trend_strength"],
        "success_probability":analysis["success_probability"]
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.patch(url,json=payload,headers=headers)

    print("Updated:",id,r.status_code)


# ==============================
# MAIN
# ==============================

def main():

    ideas = load_ideas()

    if not ideas:
        print("No ideas to analyze")
        return

    for idea in ideas[:5]:

        print("Analyzing:",idea["problem"])

        analysis = analyze_market(
            idea["problem"],
            idea["solution"]
        )

        if analysis:

            update_idea(
                idea["id"],
                analysis
            )


if __name__ == "__main__":

    main()
