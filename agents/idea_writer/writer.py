import os
import time
import json
import requests
import re


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


BATCH_SIZE = 20
DELAY = 0.8
MAX_RETRY = 3


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# -----------------------------
# FETCH UNPROCESSED SIGNALS
# -----------------------------

def fetch_signals():

    url = f"{SUPABASE_URL}/rest/v1/signals"

    params = {
        "processed": "eq.false",
        "limit": BATCH_SIZE
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        print("Fetch failed:", r.text)
        return []

    return r.json()


# -----------------------------
# INSERT IDEA
# -----------------------------

def insert_idea(data):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    r = requests.post(
        url,
        headers=headers,
        json=data
    )

    if r.status_code not in [200, 201]:
        print("Insert failed:", r.text)


# -----------------------------
# MARK SIGNAL PROCESSED
# -----------------------------

def mark_processed(signal_id):

    url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{signal_id}"

    r = requests.patch(
        url,
        headers=headers,
        json={"processed": True}
    )

    if r.status_code not in [200, 204]:
        print("Update failed:", r.text)


# -----------------------------
# LLM CALL WITH RETRY
# -----------------------------

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


# -----------------------------
# PROMPT
# -----------------------------

def build_prompt(title, content):

    return f"""
You are a startup founder and market analyst.

Analyze the signal below and extract a startup opportunity.

Return STRICT JSON only.

Fields:

problem
solution
market
audience
revenue_model
moat
market_size
competition

Signal Title:
{title}

Signal Content:
{content}
"""


# -----------------------------
# CLEAN JSON FROM LLM
# -----------------------------

def clean_json(text):

    text = text.strip()

    text = re.sub(r"^```json", "", text)
    text = re.sub(r"```$", "", text)

    return text.strip()


# -----------------------------
# PARSE JSON
# -----------------------------

def parse_response(text):

    try:
        cleaned = clean_json(text)
        return json.loads(cleaned)

    except Exception as e:

        print("JSON parse failed:", e)

        return None


# -----------------------------
# MAIN
# -----------------------------

def main():

    signals = fetch_signals()

    print("Signals to process:", len(signals))

    processed = 0

    for s in signals:

        signal_id = s["id"]
        title = s["title"]
        content = s.get("content", "")

        prompt = build_prompt(title, content)

        response = call_llm(prompt)

        if not response:
            continue

        parsed = parse_response(response)

        if not parsed:
            continue

        idea_data = {
            "problem": parsed.get("problem"),
            "solution": parsed.get("solution"),
            "market": parsed.get("market"),
            "audience": parsed.get("audience"),
            "revenue_model": parsed.get("revenue_model"),
            "moat": parsed.get("moat"),
            "market_size": parsed.get("market_size"),
            "competition": parsed.get("competition")
        }

        insert_idea(idea_data)

        mark_processed(signal_id)

        processed += 1

        print("Idea created from signal:", signal_id)

        time.sleep(DELAY)

    print("Processed:", processed)


if __name__ == "__main__":
    main()
