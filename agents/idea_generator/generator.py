import os
import requests
import re
import random
import time

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ================================
# MODEL POOL (large fallback list)
# ================================

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
"google/gemma-3n-e2b-it:free"
]

MAX_SIGNALS = 12
MAX_IDEAS = 10


# ================================
# LOAD SIGNALS
# ================================

def load_signals():

    url = f"{SUPABASE_URL}/rest/v1/signals?select=title&limit={MAX_SIGNALS}"

    r = requests.get(url, headers=SUPABASE_HEADERS)

    if r.status_code != 200:
        print("Failed loading signals:", r.text)
        return []

    return r.json()


# ================================
# DISCOVER EXTRA FREE MODELS
# ================================

def discover_free_models():

    url = "https://openrouter.ai/api/v1/models"

    try:

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

    except:
        return []


# ================================
# CALL AI (robust fallback system)
# ================================

def call_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = MODEL_LIST.copy()
    random.shuffle(models)

    for model in models:

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

            return data["choices"][0]["message"]["content"]

        except:
            continue

    print("Primary models failed — discovering new ones")

    extra_models = discover_free_models()
    random.shuffle(extra_models)

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

            return data["choices"][0]["message"]["content"]

        except:
            continue

    return None


# ================================
# PARSE IDEAS
# ================================

def parse_ideas(text):

    ideas = []

    for line in text.split("\n"):

        line = line.strip()

        if re.match(r"^\d+[\.\)]", line):

            idea = re.sub(r"^\d+[\.\)]\s*", "", line)

            ideas.append(idea)

    return ideas


# ================================
# FILTER IDEAS
# ================================

def filter_ideas(ideas):

    filtered = []

    for idea in ideas:

        idea = idea.strip()

        if len(idea) < 25:
            continue

        idea = idea.replace('"', "")

        if idea.lower().startswith("build a"):
            idea = idea[7:]

        if idea not in filtered:
            filtered.append(idea)

    return filtered[:MAX_IDEAS]


# ================================
# LOAD EXISTING IDEAS
# ================================

def load_existing_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=idea"

    r = requests.get(url, headers=SUPABASE_HEADERS)

    if r.status_code != 200:
        return []

    data = r.json()

    return [x["idea"].lower() for x in data]


# ================================
# REMOVE DUPLICATES
# ================================

def remove_duplicates(new_ideas, existing):

    unique = []

    for idea in new_ideas:

        if idea.lower() not in existing:
            unique.append(idea)

    return unique


# ================================
# SAVE IDEAS
# ================================

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
            print("Saved idea:", idea)


# ================================
# GENERATE IDEAS
# ================================

def generate_ideas(signals):

    if not signals:
        return []

    headlines = [s["title"] for s in signals]

    print("\nSignals used for idea generation:\n")

    for h in headlines:
        print("-", h)

    joined = "\n".join(headlines)

    prompt = f"""
You are a venture capitalist researching emerging technology markets.

Based on the following signals, identify startup opportunities.

Signals:
{joined}

Rules:

- focus on real problems
- avoid generic AI ideas
- focus on emerging markets
- each idea must describe a real product

Return a numbered list of startup ideas.
"""

    response = call_ai(prompt)

    if not response:
        return []

    ideas = parse_ideas(response)

    ideas = filter_ideas(ideas)

    return ideas


# ================================
# MAIN PIPELINE
# ================================

if __name__ == "__main__":

    print("\nLoading signals...\n")

    signals = load_signals()

    print("Signals loaded:", len(signals))

    if not signals:
        exit()

    ideas = generate_ideas(signals)

    if not ideas:
        print("No ideas generated")
        exit()

    print("\nGenerated ideas:\n")

    for i in ideas:
        print("-", i)

    existing = load_existing_ideas()

    ideas = remove_duplicates(ideas, existing)

    if not ideas:
        print("\nAll generated ideas already exist")
        exit()

    print("\nSaving ideas to database...\n")

    save_ideas(ideas)

    print("\nIdea generation pipeline completed\n")
