import os
import time
import requests


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


BATCH_SIZE = 100
DELAY = 0.7
MAX_RETRY = 3


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# -----------------------------------
# FETCH IDEAS WITHOUT SOLUTION
# -----------------------------------

def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    params = {
        "solution": "is.null",
        "limit": BATCH_SIZE
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        print("Fetch failed:", r.text)
        return []

    return r.json()


# -----------------------------------
# UPDATE IDEA
# -----------------------------------

def update_idea(idea_id, data):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    r = requests.patch(
        url,
        headers=headers,
        json=data
    )

    if r.status_code not in [200, 204]:
        print("Update failed:", r.text)


# -----------------------------------
# CALL LLM WITH RETRY
# -----------------------------------

def call_llm(prompt):

    for attempt in range(MAX_RETRY):

        try:

            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60
            )

            if r.status_code == 200:

                data = r.json()

                return data["choices"][0]["message"]["content"]

            else:

                print("API error:", r.status_code)

        except Exception as e:

            print("Request error:", e)

        time.sleep(2)

    return None


# -----------------------------------
# BUILD PROMPT
# -----------------------------------

def build_prompt(problem):

    return f"""
You are a startup founder.

Based on the problem below, propose a startup idea.

Return JSON with fields:

solution
market
audience
revenue_model
moat
market_size
competition

Problem:
{problem}
"""


# -----------------------------------
# PARSE JSON (simple)
# -----------------------------------

import json


def parse_response(text):

    try:
        return json.loads(text)
    except:
        return None


# -----------------------------------
# MAIN
# -----------------------------------

def main():

    ideas = fetch_ideas()

    print("Ideas to process:", len(ideas))

    processed = 0

    for idea in ideas:

        idea_id = idea["id"]
        problem = idea["problem"]

        prompt = build_prompt(problem)

        response = call_llm(prompt)

        if response:

            parsed = parse_response(response)

            if parsed:

                update_idea(idea_id, parsed)

                processed += 1

                print("Idea written:", idea_id)

        time.sleep(DELAY)

    print("Processed:", processed)


if __name__ == "__main__":
    main()
