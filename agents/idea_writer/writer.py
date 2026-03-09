import os
import json
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def load_trends():
    with open("data/trends.json") as f:
        return json.load(f)


def save_idea(problem, solution):

    url = f"{SUPABASE_URL}/rest/v1/ideas"

    payload = {
        "problem": problem,
        "solution": solution
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("Inserted idea:", problem)
    print("Status:", r.status_code)


if __name__ == "__main__":

    trends = load_trends()

    for t in trends[:5]:

        problem = t["title"]

        solution = f"Startup solution addressing: {problem}"

        save_idea(problem, solution)
