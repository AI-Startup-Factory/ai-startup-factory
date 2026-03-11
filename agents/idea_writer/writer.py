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

# fallback model list
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

# -----------------------------
# LOAD LOCAL EMBEDDING MODEL
# -----------------------------
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# FETCH PROBLEMS WITHOUT SOLUTION
# -----------------------------
def fetch_problems():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&solution=is.null&limit=20"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


# -----------------------------
# AI CALL WITH MODEL FALLBACK
# -----------------------------
def call_ai(prompt):

    for model in MODELS:

        print("Trying model:", model)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
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

        print("Model failed:", model)

    print("All models failed")
    return None


# -----------------------------
# GENERATE EMBEDDING
# -----------------------------
def embed(text):

    vector = embedding_model.encode(text)

    return vector.tolist()


# -----------------------------
# FORMAT VECTOR FOR SUPABASE
# -----------------------------
def format_vector(v):

    return "[" + ",".join(str(x) for x in v) + "]"


# -----------------------------
# CHECK SEMANTIC DUPLICATE
# -----------------------------
def is_duplicate(vector):

    vector_str = format_vector(vector)

    sql = f"""
    SELECT problem_embedding <=> '{vector_str}'::vector AS distance
    FROM ideas
    WHERE problem_embedding IS NOT NULL
    ORDER BY problem_embedding <=> '{vector_str}'::vector
    LIMIT 1
    """

    url = f"{SUPABASE_URL}/rest/v1/rpc/sql"

    r = requests.post(url, headers=headers, json={"query": sql})

    if r.status_code != 200:
        return False

    data = r.json()

    if len(data) == 0:
        return False

    distance = data[0]["distance"]

    if distance < 0.1:
        print("Duplicate detected distance:", distance)
        return True

    return False


# -----------------------------
# UPDATE IDEA RECORD
# -----------------------------
def update_idea(idea_id, data, embedding):

    payload = {
        "solution": data.get("solution"),
        "market": data.get("market"),
        "audience": data.get("audience"),
        "revenue_model": data.get("revenue_model"),
        "moat": data.get("moat"),
        "problem_embedding": format_vector(embedding)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Updated:", idea_id)
    else:
        print("Update failed:", r.text)


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():

    problems = fetch_problems()

    if len(problems) == 0:
        print("No problems to process")
        return

    batch = [p["problem"] for p in problems]

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
{json.dumps(batch)}
"""

    print("Calling AI for", len(batch), "problems")

    result = call_ai(prompt)

    if not result:
        return

    try:
        ideas = json.loads(result)
    except:
        print("AI JSON parse error")
        return

    for idea in ideas:

        problem = idea["problem"]

        embedding = embed(problem)

        if is_duplicate(embedding):
            print("Skipped duplicate:", problem)
            continue

        for p in problems:
            if p["problem"] == problem:

                update_idea(p["id"], idea, embedding)


if __name__ == "__main__":
    main()
