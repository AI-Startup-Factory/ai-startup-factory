import requests


def fetch():

    signals = []

    url = "https://www.indiehackers.com/products?format=json"

    r = requests.get(url)

    if r.status_code != 200:
        return signals

    data = r.json()

    products = data.get("products", [])

    for p in products[:25]:

        signals.append({
            "source": "indiehackers",
            "title": p.get("name", ""),
            "content": p.get("tagline", ""),
            "url": p.get("url", ""),
            "score": p.get("votes_count", 0)
        })

    return signals
