import os
import requests
import time
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

HN_API = "https://hn.algolia.com/api/v1/search"
GITHUB_API = "https://api.github.com/search/repositories"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

REQUEST_TIMEOUT = 30


# ==========================
# LOAD IDEAS
# ==========================

def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:

        print("Failed loading ideas")

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
        "the","and","for","with","that","this",
        "from","into","using","build","system",
        "platform","software"
    ]

    keywords = []

    for w in words:

        if len(w) < 4:
            continue

        if w in stopwords:
            continue

        keywords.append(w)

    return " ".join(keywords[:5])


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

        r = requests.get(HN_API, params=params, timeout=REQUEST_TIMEOUT)

        data = r.json()

        hits = data.get("hits", [])

        score = 0

        for h in hits:

            points = h.get("points", 0)
            comments = h.get("num_comments", 0)

            score += points + comments

        return score

    except:

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

        r = requests.get(GITHUB_API, params=params, timeout=REQUEST_TIMEOUT)

        data = r.json()

        repos = data.get("items", [])

        score = 0

        for repo in repos:

            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)

            score += stars + forks

        return score

    except:

        return 0


# ==========================
# MOMENTUM CALCULATION
# ==========================

def calculate_momentum(hn, gh):

    momentum = (hn * 1.2) + (gh * 0.8)

    return int(momentum)


# ==========================
# NORMALIZE VELOCITY
# ==========================

def normalize_velocity(momentum):

    if momentum > 10000:
        return 10

    if momentum > 5000:
        return 9

    if momentum > 2000:
        return 8

    if momentum > 1000:
        return 7

    if momentum > 500:
        return 6

    if momentum > 200:
        return 5

    if momentum > 100:
        return 4

    if momentum > 50:
        return 3

    if momentum > 20:
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

        print("Analyzing:", problem)

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
