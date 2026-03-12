import os
import json
import requests
from sentence_transformers import SentenceTransformer

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_KEY:
    print("Missing environment variables")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

AI_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_KEY}",
    "Content-Type": "application/json"
}

MODELS = [
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "arcee-ai/trinity-mini:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "google/gemma-3-27b-it:free"
]

print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def fetch_problems():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&solution=is.null&limit=20"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    data = r.json()

    print("Fetched problems:", len(data))

    return data


def call_ai(prompt):

    for model in MODELS:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        r = requests.post(OPENROUTER_URL, headers=AI_HEADERS, json=payload)

        if r.status_code == 200:

            data = r.json()

            try:
                content = data["choices"][0]["message"]["content"]
                print("Success with:", model)
                return content
            except:
                pass

        print("Model failed")

    print("All models failed")
    return None


def clean_json(text):

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    return text


def embed_batch(texts):

    print("Generating embeddings...")

    vectors = embedding_model.encode(texts)

    result = []

    for v in vectors:
        result.append([float(x) for x in v])

    return result


def vector_to_pg(v):

    return "[" + ",".join(str(x) for x in v) + "]"


def update_idea(idea_id, data, embedding):

    payload = {
        "solution": data.get("solution"),
        "market": data.get("market"),
        "audience": data.get("audience"),
        "revenue_model": data.get("revenue_model"),
        "moat": data.get("moat"),
        "problem_embedding": vector_to_pg(embedding)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Updated idea:", idea_id)
    else:
        print("Update failed:", r.text)


def main():

    problems = fetch_problems()

    if not problems:
        print("No problems found")
        return

    problem_texts = [p["problem"] for p in problems]

    problem_map = {p["problem"]: p["id"] for p in problems}

    prompt = f"""
Generate startup solutions for the following problems.

Return ONLY JSON array.

Each item must contain:
problem
solution
market
audience
revenue_model
moat

Problems:
{json.dumps(problem_texts)}
"""

    result = call_ai(prompt)

    if not result:
        return

    result = clean_json(result)

    try:
        ideas = json.loads(result)
    except Exception as e:
        print("JSON parse error:", e)
        print(result)
        return

    idea_problems = [idea["problem"] for idea in ideas]

    embeddings = embed_batch(idea_problems)

    for idea, embedding in zip(ideas, embeddings):

        problem = idea["problem"]

        if problem not in problem_map:
            print("Problem mismatch:", problem)
            continue

        idea_id = problem_map[problem]

        update_idea(idea_id, idea, embedding)


if __name__ == "__main__":
    main()
