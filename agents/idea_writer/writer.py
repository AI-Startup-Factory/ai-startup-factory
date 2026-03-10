import os
import json
import requests
import sys

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ===============================
# PRIMARY MODEL PRIORITY LIST
# ===============================

MODEL_LIST = [
"stepfun/step-3.5-flash:free",
"arcee-ai/trinity-large-preview:free",
"z-ai/glm-4.5-air:free",
"nvidia/nemotron-3-nano-30b-a3b:free",
"arcee-ai/trinity-mini:free",
"nvidia/nemotron-nano-9b-v2:free",
"nvidia/nemotron-nano-12b-v2-vl:free",
"openai/gpt-oss-120b:free",
"meta-llama/llama-3.3-70b-instruct:free",
"qwen/qwen3-coder:free",
"qwen/qwen3-next-80b-a3b-instruct:free",
"openai/gpt-oss-20b:free",
"liquid/lfm-2.5-1.2b-thinking:free",
"google/gemma-3-27b-it:free",
"liquid/lfm-2.5-1.2b-instruct:free",
"mistralai/mistral-small-3.1-24b-instruct:free",
"cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
"qwen/qwen3-4b:free",
"meta-llama/llama-3.2-3b-instruct:free",
"nousresearch/hermes-3-llama-3.1-405b:free",
"google/gemma-3-4b-it:free",
"google/gemma-3n-e4b-it:free",
"google/gemma-3-12b-it:free",
"google/gemma-3n-e2b-it:free",
"nvidia/llama-nemotron-embed-vl-1b-v2:free"
]


# ===============================
# ENV CHECK
# ===============================

def check_env():
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_API_KEY:
        print("Missing environment variables")
        sys.exit(1)


# ===============================
# LOAD TRENDS
# ===============================

def load_trends():
    with open("data/trends.json") as f:
        return json.load(f)


# ===============================
# CHECK DUPLICATE IN SUPABASE
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
# AUTO DISCOVER FREE MODELS
# ===============================

def discover_free_models():

    print("Discovering free models from OpenRouter...")

    url = "https://openrouter.ai/api/v1/models"

    r = requests.get(url)

    if r.status_code != 200:
        print("Failed fetching model list")
        return []

    models = r.json()["data"]

    discovered = []

    for m in models:

        model_id = m["id"]

        if ":free" in model_id and model_id not in MODEL_LIST:

            discovered.append(model_id)

    print("Discovered", len(discovered), "extra free models")

    return discovered


# ===============================
# BATCH AI REQUEST
# ===============================

def generate_batch_analysis(problems):

    url = "https://openrouter.ai/api/v1/chat/completions"

    joined = "\n".join([f"{i+1}. {p}" for i, p in enumerate(problems)])

    prompt = f"""
Analyze the following problems and propose startup opportunities.

Problems:
{joined}

Return ONLY JSON array.

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

    # ===============================
    # TRY PRIMARY MODELS
    # ===============================

    for model in MODEL_LIST:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:

            r = requests.post(url, headers=headers, json=payload, timeout=90)

            if r.status_code != 200:
                print("Model failed:", model)
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json", "").replace("```", "").strip()

            result = json.loads(content)

            print("Success with:", model)

            return result

        except Exception as e:

            print("Error with:", model)

            continue


    # ===============================
    # DISCOVER NEW FREE MODELS
    # ===============================

    extra_models = discover_free_models()

    for model in extra_models:

        print("Trying discovered model:", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:

            r = requests.post(url, headers=headers, json=payload, timeout=90)

            if r.status_code != 200:
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json", "").replace("```", "").strip()

            result = json.loads(content)

            print("Success with discovered model:", model)

            return result

        except:
            continue


    print("All models failed")

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

        print("No new ideas")

        return

    print("Calling AI for", len(problems), "problems")

    results = generate_batch_analysis(problems)

    if not results:

        print("AI generation failed")

        return

    for item in results:

        save_to_supabase(item)


if __name__ == "__main__":

    main()
