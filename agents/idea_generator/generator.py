import os
import requests
import re

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

MODEL_LIST = [
"stepfun/step-3.5-flash:free",
"arcee-ai/trinity-large-preview:free",
"z-ai/glm-4.5-air:free",
"nvidia/nemotron-3-nano-30b-a3b:free",
"arcee-ai/trinity-mini:free",
"nvidia/nemotron-nano-9b-v2:free",
"openai/gpt-oss-120b:free",
"meta-llama/llama-3.3-70b-instruct:free",
"qwen/qwen3-coder:free",
"openai/gpt-oss-20b:free",
"google/gemma-3-27b-it:free",
"mistralai/mistral-small-3.1-24b-instruct:free",
"qwen/qwen3-4b:free",
"meta-llama/llama-3.2-3b-instruct:free",
"google/gemma-3-4b-it:free",
"google/gemma-3-12b-it:free"
]


# ==============================
# LOAD SIGNALS FROM SUPABASE
# ==============================

def load_posts():

    url = f"{SUPABASE_URL}/rest/v1/signals?select=title&limit=25"

    r = requests.get(url, headers=SUPABASE_HEADERS)

    if r.status_code != 200:
        print("Failed loading signals:", r.text)
        return []

    data = r.json()

    return data


# ==============================
# DISCOVER EXTRA FREE MODELS
# ==============================

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


# ==============================
# CALL AI
# ==============================

def call_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
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

    # Discover new models
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


# ==============================
# PARSE IDEAS
# ==============================

def parse_ideas(text):

    ideas = []

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if re.match(r"^\d+[\.\)]", line):

            idea = re.sub(r"^\d+[\.\)]\s*", "", line)

            ideas.append(idea)

    return ideas


# ==============================
# SAVE IDEAS TO SUPABASE
# ==============================

def save_ideas(ideas):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    for idea in ideas:

        payload = {
            "idea": idea
        }

        r = requests.post(url, headers=SUPABASE_HEADERS, json=payload)

        if r.status_code not in [200, 201]:
            print("Insert failed:", r.text)
        else:
            print("Inserted idea")


# ==============================
# GENERATE IDEAS
# ==============================

def generate_ideas(posts):

    if not posts:
        return []

    headlines = [p["title"] for p in posts[:5]]

    print("\nHeadlines used for generation:")

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
        print("AI generation failed")
        return []

    ideas = parse_ideas(response)

    return ideas


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    print("Loading signals...")

    posts = load_posts()

    print("Signals loaded:", len(posts))

    ideas = generate_ideas(posts)

    if not ideas:
        print("No ideas generated")
        exit()

    print("\nGenerated Ideas:")

    for idea in ideas:
        print("-", idea)

    print("\nSaving ideas to database...")

    save_ideas(ideas)

    print("\nIdea generation completed")
