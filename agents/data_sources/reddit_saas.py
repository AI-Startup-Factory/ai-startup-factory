import requests


def fetch():

    signals = []

    url = "https://www.reddit.com/r/SaaS/hot.json?limit=25"

    headers = {"User-Agent": "startup-radar"}

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return signals

    posts = r.json()["data"]["children"]

    for p in posts:

        d = p["data"]

        signals.append({
            "source": "reddit_saas",
            "title": d["title"],
            "content": d.get("selftext", ""),
            "url": f"https://reddit.com{d['permalink']}",
            "score": d.get("score", 0)
        })

    return signals
