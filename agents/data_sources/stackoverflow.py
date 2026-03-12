import requests


def fetch():

    signals = []

    url = "https://api.stackexchange.com/2.3/questions?order=desc&sort=votes&site=stackoverflow"

    r = requests.get(url)

    if r.status_code != 200:
        return signals

    data = r.json()

    for q in data.get("items", [])[:25]:

        signals.append({
            "source": "stackoverflow",
            "title": q["title"],
            "content": "",
            "url": q["link"],
            "score": q["score"]
        })

    return signals
