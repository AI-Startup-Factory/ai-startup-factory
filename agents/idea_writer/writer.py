import os
import json
import requests
import sys

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


def check_env():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Missing Supabase environment variables")
        print("SUPABASE_URL:", SUPABASE_URL)
        print("SUPABASE_ANON_KEY:", "SET" if SUPABASE_KEY else "MISSING")
        sys.exit(1)


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
        "Prefer": "return=representation"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("Inserted idea:", problem)
    print("Status:", r.status_code)

    if r.text:
        print("Response:", r.text)


if __name__ == "__main__":

    check_env()

    trends = load_trends()

    for t in trends[:5]:

        problem = t.get("title", "Unknown problem")

        solution = f"Startup solution addressing: {problem}"

        save_idea(problem, solution)
