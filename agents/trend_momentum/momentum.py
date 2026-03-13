import os
import requests
import time
import re
import math


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# GitHub token dari GitHub Actions secret
GITHUB_TOKEN = os.getenv("AI_STARTUP_TOKEN")


HN_API = "https://hn.algolia.com/api/v1/search"
GITHUB_API = "https://api.github.com/search/repositories"


REQUEST_TIMEOUT = 30


SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


# ==========================
# LOAD IDEAS
# ==========================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem"

    r = requests.get(url, headers=SUPABASE_HEADERS)

    if r.status_code != 200:
        print("Failed loading ideas:", r.text)
        return []

    return r.json()


# ==========================
# KEYWORD EXTRACTION
# ==========================

def extract_keywords(text):

    text = text.lower()

    text = re.sub(r"[^a-z0-9\s]", "", text)

    words = text.split()

    stopwords = [
        "the","and","for","with","that","this","from",
        "into","using","build","system","platform",
        "software","current","existing","methods",
        "approach","model","models","data","based",
        "analysis","problem","solution","applications"
    ]

    keywords = []

    for w in words:

        if len(w) < 4:
            continue

        if w in stopwords:
            continue

        keywords.append(w)

    return " ".join(keywords[:3])


# ==========================
# HACKERNEWS MOMENTUM
# ==========================

def hn_score(query):

    try:

        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": 10
        }

        r = requests.get(
            HN_API,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        if r.status_code != 200:
            print("HN error:", r.text)
            return 0

        data = r.json()

        hits = data.get("hits", [])

        score = 0

        for h in hits:

            points = h.get("points", 0)
            comments = h.get("num_comments", 0)

            score += points + comments

        return score

    except Exception as e:

        print("HN exception:", e)

        return 0


# ==========================
# GITHUB MOMENTUM
# ==========================

def github_score(query):

    try:

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }

        r = requests.get(
            GITHUB_API,
            headers=GITHUB_HEADERS,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        if r.status_code != 200:
            print("GitHub API error:", r.text)
            return 0

        data = r.json()

        repos = data.get("items", [])

        score = 0

        for repo in repos:

            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)

            score += stars + forks

        return score

    except Exception as e:

        print("GitHub exception:", e)

        return 0


# ==========================
# MOMENTUM CALCULATION
# ==========================

def calculate_momentum(hn, gh):

    hn_component = math.log1p(hn) * 3
    gh_component = math.log1p(gh) * 2

    momentum = hn_component + gh_component

    return int(momentum)


# ==========================
# VELOCITY NORMALIZATION
# ==========================

def normalize_velocity(momentum):

    if momentum > 2000:
        return 10

    if momentum > 1000:
        return 9

    if momentum > 500:
        return 8

    if momentum > 200:
        return 7

    if momentum > 100:
        return 6

    if momentum > 50:
        return 5

    if momentum > 20:
        return 4

    if momentum > 10:
        return 3

    if momentum > 5:
        return 2

    return 1


# ==========================
# UPDATE DATABASE
# ==========================

def update_db(idea_id, hn, gh, momentum, velocity):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"

    payload = {
        "hn_score": hn,
        "github_score": gh,
        "momentum_score": momentum,
        "trend_velocity": velocity
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.patch(url, json=payload, headers=headers)

    print("Updated:", idea_id, r.status_code)


# ==========================
# MAIN
# ==========================

def main():

    ideas = load_ideas()

    if not ideas:
        print("No ideas found")
        return

    for idea in ideas:

        problem = idea["problem"]

        print("\nAnalyzing:", problem)

        keywords = extract_keywords(problem)

        print("Keywords:", keywords)

        hn = hn_score(keywords)

        gh = github_score(keywords)

        momentum = calculate_momentum(hn, gh)

        velocity = normalize_velocity(momentum)

        print("HN:", hn)
        print("GitHub:", gh)
        print("Momentum:", momentum)
        print("Velocity:", velocity)

        update_db(
            idea["id"],
            hn,
            gh,
            momentum,
            velocity
        )

        time.sleep(1)


if __name__ == "__main__":

    main()
