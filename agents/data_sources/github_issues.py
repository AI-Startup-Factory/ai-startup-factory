import requests


def fetch():

    signals = []

    url = "https://api.github.com/search/issues?q=label:enhancement&sort=comments&order=desc"

    r = requests.get(url)

    if r.status_code != 200:
        return signals

    data = r.json()

    for issue in data.get("items", [])[:25]:

        signals.append({
            "source": "github_issues",
            "title": issue["title"],
            "content": issue.get("body", ""),
            "url": issue["html_url"],
            "score": issue.get("comments", 0)
        })

    return signals
