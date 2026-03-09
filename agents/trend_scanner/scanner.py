import requests


def fetch_reddit():
    url = "https://www.reddit.com/r/startups.json"

    headers = {
        "User-Agent": "Mozilla/5.0 (AIStartupFactoryBot)"
    }

    res = requests.get(url, headers=headers, timeout=10)

    if res.status_code != 200:
        print("Failed to fetch Reddit:", res.status_code)
        return []

    try:
        data = res.json()
    except Exception as e:
        print("JSON error:", e)
        print("Response text:", res.text[:200])
        return []

    posts = []

    for post in data["data"]["children"]:
        title = post["data"]["title"]
        posts.append(title)

    return posts


if __name__ == "__main__":
    posts = fetch_reddit()

    print("Fetched posts:")

    for p in posts[:10]:
        print("-", p)
