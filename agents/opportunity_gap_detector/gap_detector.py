import os
import requests
import numpy as np
from collections import defaultdict

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing environment variables")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# -----------------------------
# FETCH IDEAS
# -----------------------------
def fetch_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,cluster_id,cluster_size,trend_strength,market_size,competition"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("Fetch error:", r.text)
        return []

    data = r.json()

    print("Fetched ideas:", len(data))

    return data


# -----------------------------
# MARKET SIZE NORMALIZATION
# -----------------------------
def normalize_market_size(v):

    if not v:
        return 0.5

    v = str(v).lower()

    if "trillion" in v:
        return 1.0

    if "billion" in v:
        return 0.8

    if "million" in v:
        return 0.5

    return 0.3


# -----------------------------
# COMPETITION NORMALIZATION
# -----------------------------
def normalize_competition(v):

    if not v:
        return 0.5

    v = str(v).lower()

    if "high" in v:
        return 0.2

    if "medium" in v:
        return 0.5

    if "low" in v:
        return 0.8

    return 0.5


# -----------------------------
# UPDATE IDEA
# -----------------------------
def update_row(row_id, density, momentum, score):

    payload = {
        "cluster_density": density,
        "cluster_momentum": momentum,
        "cluster_opportunity_score": score,
        "opportunity_gap_score": int(score * 100)
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"

    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print("Updated opportunity:", row_id)
    else:
        print("Update failed:", r.text)


# -----------------------------
# MAIN ANALYSIS
# -----------------------------
def main():

    ideas = fetch_ideas()

    if not ideas:
        print("No ideas found")
        return

    clusters = defaultdict(list)

    for i in ideas:

        cid = i.get("cluster_id")

        if cid is None:
            continue

        clusters[cid].append(i)

    print("Clusters detected:", len(clusters))

    cluster_scores = {}

    for cid, rows in clusters.items():

        size = len(rows)

        density = min(1.0, size / 20)

        trend_values = [
            r.get("trend_strength", 0) or 0
            for r in rows
        ]

        momentum = np.mean(trend_values) / 100 if trend_values else 0.3

        market_scores = [
            normalize_market_size(r.get("market_size"))
            for r in rows
        ]

        market_score = np.mean(market_scores)

        competition_scores = [
            normalize_competition(r.get("competition"))
            for r in rows
        ]

        competition_score = np.mean(competition_scores)

        opportunity = (
            (1 - density) * 0.35 +
            momentum * 0.25 +
            market_score * 0.25 +
            competition_score * 0.15
        )

        cluster_scores[cid] = {
            "density": density,
            "momentum": momentum,
            "score": opportunity
        }

    for i in ideas:

        cid = i.get("cluster_id")

        if cid not in cluster_scores:
            continue

        s = cluster_scores[cid]

        update_row(
            i["id"],
            s["density"],
            s["momentum"],
            s["score"]
        )

    print("Opportunity analysis complete")


if __name__ == "__main__":
    main()
