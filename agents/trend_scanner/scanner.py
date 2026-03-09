import requests

def fetch_reddit():
    url = "https://www.reddit.com/r/startups.json"
    headers = {"User-Agent": "ai-startup-factory"}

    res = requests.get(url, headers=headers)
    data = res.json()

    posts = []

    for post in data["data"]["children"]:
        title = post["data"]["title"]
        posts.append(title)

    return posts


if __name__ == "__main__":
    posts = fetch_reddit()

    for p in posts[:10]:
        print(p)
