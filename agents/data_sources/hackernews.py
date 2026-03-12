import requests


def fetch():

    signals = []

    url = "https://hacker-news.firebaseio.com/v0/topstories.json"

    story_ids = requests.get(url).json()[:30]

    for sid in story_ids:

        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        ).json()

        if not item or "title" not in item:
            continue

        signals.append({
            "source": "hackernews",
            "title": item["title"],
            "content": item.get("text", ""),
            "url": item.get("url", ""),
            "score": item.get("score", 0)
        })

    return signals
