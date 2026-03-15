import os
import requests
import json

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def fetch_clusters():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem,cluster_id"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    return r.json()


def group_clusters(rows):

    clusters = {}

    for r in rows:

        cid = r.get("cluster_id")

        if not cid:
            continue

        if cid not in clusters:
            clusters[cid] = []

        clusters[cid].append(r["problem"])

    return clusters


def detect_gap(problems):

    text = "\n".join(problems)

    prompt = f"""
You are a startup opportunity analyst.

These problems belong to the same technology cluster.

Problems:
{text}

Identify missing adjacent startup opportunities
that are NOT listed but logically belong here.

Return bullet list.
"""

    return prompt


def main():

    rows = fetch_clusters()

    clusters = group_clusters(rows)

    for cid, problems in clusters.items():

        if len(problems) < 3:
            continue

        prompt = detect_gap(problems)

        print("\nCluster:", cid)
        print(prompt)


if __name__ == "__main__":
    main()
