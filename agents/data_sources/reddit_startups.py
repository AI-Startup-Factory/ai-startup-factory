import requests


def fetch():

    signals = []

    url = "https://www.reddit.com/r/startups/hot.json?limit=25"

    headers = {"User-Agent": "startup-radar"}

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return signals

    posts = r.json()["data"]["children"]

    for p in posts:

        data = p["data"]

        signals.append({
            "source": "reddit_startups",
            "title": data["title"],
            "content": data.get("selftext", ""),
            "url": f"https://reddit.com{data['permalink']}",
            "score": data.get("score", 0)
        })

    return signals
