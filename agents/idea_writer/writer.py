import os
import requests
import json

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
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"

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
"openai/gpt-oss-120b:free",
"meta-llama/llama-3.3-70b-instruct:free",
"qwen/qwen3-next-80b-a3b-instruct:free",
"google/gemma-3-27b-it:free"
]


# -----------------------------
# FETCH PROBLEMS WITHOUT SOLUTION
# -----------------------------
def fetch_problems():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&solution=is.null&limit=20"

    r = requests.get(url, headers=headers)

    return r.json()


# -----------------------------
# AI CALL WITH FALLBACK
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

    print("All models failed")
    return None


# -----------------------------
# GENERATE EMBEDDING
# -----------------------------
def embed(text):

    payload = {
        "model": "text-embedding-3-small",
        "input": text
    }

    r = requests.post(EMBEDDING_URL, headers=AI_HEADERS, json=payload)

    if r.status_code != 200:
        return None

    data = r.json()

    return data["data"][0]["embedding"]


# -----------------------------
# CHECK SEMANTIC DUPLICATE
# -----------------------------
def is_duplicate(embedding):

    vector = str(embedding)

    query = f"""
    SELECT problem_embedding <=> '{vector}'::vector AS distance
    FROM ideas
    WHERE problem_embedding IS NOT NULL
    ORDER BY problem_embedding <=> '{vector}'::vector
    LIMIT 1
    """

    url = f"{SUPABASE_URL}/rest/v1/rpc/sql"

    r = requests.post(url, headers=headers, json={"query": query})

    if r.status_code != 200:
        return False

    data = r.json()

    if len(data) == 0:
        return False

    distance = data[0]["distance"]

    if distance < 0.1:
        print("Duplicate detected (distance:", distance, ")")
        return True

    return False


# -----------------------------
# INSERT IDEA
# -----------------------------
def insert_idea(idea_id, solution, embedding):

    payload = {
        "solution": solution,
        "problem_embedding": embedding
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200,204]:
        print("Inserted:", idea_id)
    else:
        print("Insert failed:", r.text)


# -----------------------------
# MAIN
# -----------------------------
def main():

    problems = fetch_problems()

    if len(problems) == 0:
        print("No problems to process")
        return

    batch = [p["problem"] for p in problems]

    prompt = f"""
Generate startup solutions for these problems.

Return JSON list with:
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

    for item in ideas:

        problem = item["problem"]
        solution = item["solution"]

        embedding = embed(problem)

        if embedding is None:
            continue

        if is_duplicate(embedding):
            continue

        for p in problems:
            if p["problem"] == problem:

                insert_idea(p["id"], solution, embedding)


if __name__ == "__main__":
    main()
