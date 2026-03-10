import os
import requests
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# =============================
# LOAD IDEAS
# =============================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return []

    return r.json()


# =============================
# SEARCH HACKERNEWS
# =============================

def hn_score(query):

    try:

        url = f"https://hn.algolia.com/api/v1/search?query={query}"

        r = requests.get(url)

        data = r.json()

        hits = data["hits"]

        score = 0

        for h in hits[:5]:

            points = h.get("points",0)
            comments = h.get("num_comments",0)

            score += points + comments

        return score

    except:

        return 0


# =============================
# SEARCH GITHUB
# =============================

def github_score(query):

    try:

        url = f"https://api.github.com/search/repositories?q={query}&sort=stars"

        r = requests.get(url)

        data = r.json()

        items = data.get("items",[])

        score = 0

        for repo in items[:3]:

            stars = repo.get("stargazers_count",0)
            forks = repo.get("forks_count",0)

            score += stars + forks

        return score

    except:

        return 0


# =============================
# NORMALIZE SCORE
# =============================

def normalize(value):

    if value > 5000:
        return 10

    if value > 2000:
        return 9

    if value > 1000:
        return 8

    if value > 500:
        return 7

    if value > 200:
        return 6

    if value > 100:
        return 5

    if value > 50:
        return 4

    if value > 20:
        return 3

    if value > 10:
        return 2

    return 1


# =============================
# UPDATE SUPABASE
# =============================

def update_trend(idea_id,trend):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    payload = {
        "trend_strength": trend
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":"application/json"
    }

    requests.patch(url,json=payload,headers=headers)


# =============================
# MAIN
# =============================

def main():

    ideas = load_ideas()

    for idea in ideas:

        problem = idea["problem"]

        print("Analyzing momentum:",problem)

        hn = hn_score(problem)

        gh = github_score(problem)

        raw_score = hn + gh

        trend = normalize(raw_score)

        update_trend(idea["id"],trend)

        time.sleep(1)


if __name__ == "__main__":
    main()
