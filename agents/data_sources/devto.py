import requests


def fetch():

    signals = []

    url = "https://dev.to/api/articles?top=7"

    r = requests.get(url)

    if r.status_code != 200:
        return signals

    posts = r.json()

    for p in posts:

        signals.append({
            "source": "devto",
            "title": p["title"],
            "content": p.get("description", ""),
            "url": p["url"],
            "score": p.get("positive_reactions_count", 0)
        })

    return signals
