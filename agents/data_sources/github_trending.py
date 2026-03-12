import requests


def fetch():

    signals = []

    url = "https://ghapi.huchen.dev/repositories"

    r = requests.get(url)

    if r.status_code != 200:
        return signals

    repos = r.json()

    for repo in repos:

        signals.append({
            "source": "github_trending",
            "title": repo["name"],
            "content": repo.get("description", ""),
            "url": repo["url"],
            "score": repo.get("stars", 0)
        })

    return signals
