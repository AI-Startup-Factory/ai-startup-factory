import requests


def fetch_hackernews():
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"

    res = requests.get(url)

    if res.status_code != 200:
        print("Failed to fetch HN stories")
        return []

    story_ids = res.json()[:10]

    posts = []

    for sid in story_ids:
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        story = requests.get(story_url).json()

        if story and "title" in story:
            posts.append(story["title"])

    return posts


if __name__ == "__main__":

    posts = fetch_hackernews()

    print("Fetched HackerNews posts:")

    for p in posts:
        print("-", p)
