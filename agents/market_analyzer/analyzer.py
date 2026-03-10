import os
import json
import requests
import re
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

BATCH_SIZE = 10

MODEL_LIST = [
"stepfun/step-3.5-flash:free",
"arcee-ai/trinity-large-preview:free",
"z-ai/glm-4.5-air:free",
"nvidia/nemotron-3-nano-30b-a3b:free"
]

# =========================
# JSON EXTRACTOR
# =========================

def extract_json(text):

    try:

        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return json.loads(match.group())

    except Exception as e:
        print("JSON extraction error:", e)

    return None


# =========================
# LOAD IDEAS FROM SUPABASE
# =========================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?trend_strength=is.null&select=id,problem"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Failed to fetch ideas:", r.text)
        return []

    return r.json()


# =========================
# DISCOVER FREE MODELS
# =========================

def discover_models():

    print("Checking OpenRouter free models")

    try:

        r = requests.get("https://openrouter.ai/api/v1/models")

        data = r.json()

        models = []

        for m in data["data"]:

            if ":free" in m["id"]:

                if m["id"] not in MODEL_LIST:
                    models.append(m["id"])

        return models

    except:
        return []


# =========================
# CALL AI
# =========================

def call_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = MODEL_LIST + discover_models()

    for model in models:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages":[
                {"role":"user","content":prompt}
            ]
        }

        try:

            r = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )

            if r.status_code != 200:
                print("Model error:", r.status_code)
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json","").replace("```","").strip()

            parsed = extract_json(content)

            if parsed:
                print("AI success with:", model)
                return parsed

        except Exception as e:

            print("Model failed:", model, e)

        time.sleep(2)

    return None


# =========================
# UPDATE SUPABASE
# =========================

def update_idea(idea_id, analysis):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    payload = {
        "market_size": analysis.get("market_size"),
        "competition": analysis.get("competition"),
        "trend_strength": analysis.get("trend_strength"),
        "success_probability": analysis.get("success_probability")
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.patch(url, json=payload, headers=headers)

    print("Updated:", idea_id, r.status_code)


# =========================
# BUILD PROMPT
# =========================

def build_prompt(ideas):

    problems = [idea["problem"] for idea in ideas]

    prompt = f"""
Analyze the following startup problems.

Return ONLY JSON array.

Each item must contain:

problem
market_size
competition
trend_strength (1-10)
success_probability (1-10)

Problems:

{json.dumps(problems, indent=2)}
"""

    return prompt


# =========================
# MAIN
# =========================

def main():

    ideas = load_ideas()

    if not ideas:
        print("No ideas to analyze")
        return

    batch = ideas[:BATCH_SIZE]

    print("Analyzing batch:", len(batch))

    prompt = build_prompt(batch)

    results = call_ai(prompt)

    if not results:
        print("AI analysis failed")
        return

    problem_map = {idea["problem"]:idea["id"] for idea in batch}

    for item in results:

        problem = item.get("problem")

        if problem not in problem_map:
            continue

        idea_id = problem_map[problem]

        update_idea(idea_id, item)


if __name__ == "__main__":
    main()
