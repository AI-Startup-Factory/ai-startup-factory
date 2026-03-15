import os
import requests
import json
import time
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

BATCH_SIZE = 20

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


# =====================================
# FETCH IDEAS
# =====================================

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?problem=is.null&select=id,idea&limit={BATCH_SIZE}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# =====================================
# DISCOVER FREE MODELS
# =====================================

def discover_models():

    try:

        r = requests.get("https://openrouter.ai/api/v1/models")

        if r.status_code != 200:
            return []

        data = r.json()

        models = []

        for m in data["data"]:

            if ":free" in m["id"]:

                if m["id"] not in MODEL_LIST:
                    models.append(m["id"])

        return models

    except:

        return []


# =====================================
# CALL AI
# =====================================

def call_ai(prompt):

    headers_ai = {
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
            ],
            "temperature":0.3
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

        except Exception as e:

            print("Model failed:", model, e)

        time.sleep(2)

    return None


# =====================================
# PARSE JSON
# =====================================

def parse_json(text):

    try:

        text = text.replace("```json","").replace("```","").strip()

        return json.loads(text)

    except:

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except:
                return None

    return None


# =====================================
# UPDATE IDEA
# =====================================

def update_idea(idea_id, data):

    payload = {
        "problem": data.get("problem"),
        "solution": data.get("solution"),
        "audience": data.get("audience")
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(url, json=payload, headers=headers)

    if r.status_code not in [200,204]:
        print("Update failed:", r.text)


# =====================================
# MAIN
# =====================================

def main():

    print("Running Problem Extractor")

    ideas = fetch_ideas()

    print("Ideas fetched:", len(ideas))

    for idea in ideas:

        idea_text = idea["idea"]

        prompt = f"""
Extract structured startup information.

Idea:
{idea_text}

Return JSON:

{{
"problem":"...",
"solution":"...",
"audience":"..."
}}
"""

        response = call_ai(prompt)

        if not response:
            continue

        parsed = parse_json(response)

        if not parsed:
            print("JSON parse failed")
            continue

        update_idea(
            idea["id"],
            parsed
        )

        print("Processed idea:", idea["id"])

        time.sleep(2)


if __name__ == "__main__":
    main()
