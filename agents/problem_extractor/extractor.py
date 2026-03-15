import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

MAX_SIGNALS_PER_RUN = 20

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ----------------------------------------
# HTTP SESSION WITH RETRY
# ----------------------------------------

session = requests.Session()

retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429,500,502,503,504]
)

session.mount("https://", HTTPAdapter(max_retries=retries))


# ----------------------------------------
# FETCH SIGNALS
# ----------------------------------------

def fetch_signals():

    url = f"{SUPABASE_URL}/rest/v1/signals"

    params = {
        "processed":"eq.false",
        "limit":MAX_SIGNALS_PER_RUN
    }

    r = session.get(url, headers=headers, params=params, timeout=15)

    if r.status_code != 200:
        print("Fetch failed:", r.text)
        return []

    return r.json()


# ----------------------------------------
# MARK PROCESSED
# ----------------------------------------

def mark_processed(signal_id):

    url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{signal_id}"

    session.patch(
        url,
        headers=headers,
        json={"processed":True},
        timeout=10
    )


# ----------------------------------------
# INSERT IDEA
# ----------------------------------------

def insert_idea(problem):

    payload = {
        "problem":problem
    }

    r = session.post(
        f"{SUPABASE_URL}/rest/v1/ideas",
        headers=headers,
        json=payload,
        timeout=10
    )

    if r.status_code not in [200,201]:
        print("Idea insert failed:", r.text)


# ----------------------------------------
# AI EXTRACTION
# ----------------------------------------

def extract_problem(text):

    prompt = f"""
Extract the core real-world problem from this text.

Return ONLY one concise problem sentence.

TEXT:
{text}
"""

    r = session.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model":"openai/gpt-4o-mini",
            "messages":[
                {"role":"user","content":prompt}
            ],
            "temperature":0.2
        },
        timeout=30
    )

    if r.status_code != 200:
        raise Exception("AI request failed")

    data = r.json()

    if "choices" not in data:
        raise Exception("Invalid AI response")

    return data["choices"][0]["message"]["content"].strip()


# ----------------------------------------
# MAIN
# ----------------------------------------

def main():

    print("Running Problem Extractor")

    signals = fetch_signals()

    print("Signals fetched:", len(signals))

    if not signals:
        print("No signals to process")
        return

    for s in signals:

        text = f"{s.get('title','')} {s.get('content','')}"

        try:

            problem = extract_problem(text)

            insert_idea(problem)

            mark_processed(s["id"])

            print("Extracted:", problem[:80])

        except Exception as e:

            print("Extraction failed:", e)


    print("Problem extraction finished")


if __name__ == "__main__":
    main()
