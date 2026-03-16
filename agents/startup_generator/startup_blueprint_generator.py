import os
import requests
import json
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ====================================
# PRIMARY MODEL LIST (ANTI RATE LIMIT)
# ====================================

MODEL_LIST = [

"google/gemma-3-27b-it:free",
"google/gemma-3-12b-it:free",
"google/gemma-3-4b-it:free",
"google/gemma-3n-e2b-it:free",
"mistralai/mistral-small-3.1-24b-instruct:free",
"nvidia/nemotron-3-nano-30b-a3b:free",
"nvidia/nemotron-nano-9b-v2:free",
"qwen/qwen3-4b:free",
"qwen/qwen3-coder:free",
"meta-llama/llama-3.3-70b-instruct:free",
"meta-llama/llama-3.2-3b-instruct:free",
"liquid/lfm-2.5-1.2b-thinking:free",
"liquid/lfm-2.5-1.2b-instruct:free",
"stepfun/step-3.5-flash:free",
"arcee-ai/trinity-mini:free",
"z-ai/glm-4.5-air:free",
"cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
]


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# ====================================
# FETCH HIGH SCORE IDEAS
# ====================================

def fetch_opportunities():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem,opportunity_score&opportunity_score=gte.70&startup_name=is.null&limit=10"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# ====================================
# DISCOVER EXTRA FREE MODELS
# ====================================

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


# ====================================
# CALL AI WITH FALLBACK
# ====================================

def call_ai(prompt):

    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # -----------------------------
    # Primary model list
    # -----------------------------

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

    # -----------------------------
    # Discover new models
    # -----------------------------

    print("Discovering additional free models")

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


# ====================================
# GENERATE STARTUP BLUEPRINT
# ====================================

def generate_startup(problem):

    prompt = f"""
You are a startup studio.

Create a startup concept solving this problem.

Problem:
{problem}

Return STRICT JSON format:

{{
"startup_name": "...",
"pitch": "...",
"mvp_features": [
"feature1",
"feature2",
"feature3"
],
"tech_stack": [
"frontend",
"backend",
"ai_components",
"infrastructure"
],
"go_to_market": "..."
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


# ====================================
# UPDATE DATABASE
# ====================================

def update_row(row_id, blueprint):

    payload = {
        "startup_name": blueprint["startup_name"],
        "startup_pitch": blueprint["pitch"],
        "mvp_spec": blueprint["mvp_features"],
        "tech_stack": blueprint["tech_stack"],
        "gtm_plan": blueprint["go_to_market"]
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200,204]:

        print("Startup generated:", row_id)

    else:

        print("Update failed:", r.text)


# ====================================
# MAIN
# ====================================

def main():

    rows = fetch_opportunities()

    if not rows:

        print("No high scoring ideas")

        return

    for row in rows:

        problem = row["problem"]

        print("\nGenerating startup for:", problem)

        blueprint = generate_startup(problem)

        if not blueprint:

            continue

        update_row(row["id"], blueprint)

        time.sleep(2)


if __name__ == "__main__":

    main()
