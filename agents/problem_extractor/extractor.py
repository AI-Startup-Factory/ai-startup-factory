import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def fetch_signals():

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/signals?processed=eq.false",
        headers=headers
    )

    if r.status_code != 200:
        print("Fetch failed")
        return []

    return r.json()


def mark_processed(signal_id):

    requests.patch(
        f"{SUPABASE_URL}/rest/v1/signals?id=eq.{signal_id}",
        headers=headers,
        json={"processed": True}
    )


def insert_idea(problem):

    payload = {
        "problem": problem
    }

    requests.post(
        f"{SUPABASE_URL}/rest/v1/ideas",
        headers=headers,
        json=payload
    )


def extract_problem(text):

    prompt = f"""
Extract the core real-world problem from this text.

Return only ONE concise problem statement.

TEXT:
{text}
"""

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages":[
                {"role":"user","content":prompt}
            ]
        }
    )

    data = r.json()

    return data["choices"][0]["message"]["content"].strip()


def main():

    signals = fetch_signals()

    print("Signals:", len(signals))

    for s in signals:

        text = f"{s['title']} {s.get('content','')}"

        try:

            problem = extract_problem(text)

            insert_idea(problem)

            mark_processed(s["id"])

            print("Problem extracted")

        except Exception as e:

            print("Extraction failed", e)


if __name__ == "__main__":
    main()
