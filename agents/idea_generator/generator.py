import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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


def load_posts():

    with open("data/trends.json") as f:
        return json.load(f)


# ===============================
# DISCOVER EXTRA FREE MODELS
# ===============================

def discover_free_models():

    url = "https://openrouter.ai/api/v1/models"

    r = requests.get(url)

    if r.status_code != 200:
        return []

    models = r.json()["data"]

    discovered = []

    for m in models:

        model_id = m["id"]

        if ":free" in model_id and model_id not in MODEL_LIST:

            discovered.append(model_id)

    return discovered


# ===============================
# CALL AI WITH FALLBACK
# ===============================

def call_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # primary models
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
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            return content

        except:
            continue

    # discover new models
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

            r = requests.post(url, headers=headers, json=payload, timeout=90)

            if r.status_code != 200:
                continue

            data = r.json()

            content = data["choices"][0]["message"]["content"]

            return content

        except:
            continue

    print("All models failed")

    return None


# ===============================
# GENERATE IDEAS
# ===============================

def generate_ideas(posts):

    headlines = [p["title"] for p in posts[:5]]

    print("\nHeadlines:")

    for h in headlines:
        print("-", h)

    joined = "\n".join(headlines)

    prompt = f"""
You are a startup analyst.

Based on the following technology headlines, generate startup ideas.

Headlines:
{joined}

Return a numbered list of startup ideas.
"""

    response = call_ai(prompt)

    if not response:
        return "AI generation failed"

    return response


# ===============================
# MAIN
# ===============================

if __name__ == "__main__":

    posts = load_posts()

    ideas = generate_ideas(posts)

    print("\nGenerated Ideas:\n")

    print(ideas)
