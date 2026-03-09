import requests
import json
import os

def fetch_hn():

    url = "https://hacker-news.firebaseio.com/v0/topstories.json"

    story_ids = requests.get(url).json()[:10]

    posts = []

    for sid in story_ids:

        item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        item = requests.get(item_url).json()

        if item and "title" in item:
            posts.append({
                "title": item["title"],
                "url": item.get("url", "")
            })

    return posts


def save_posts(posts):

    os.makedirs("data", exist_ok=True)

    with open("data/trends.json", "w") as f:
        json.dump(posts, f, indent=2)


if __name__ == "__main__":

    posts = fetch_hn()

    print("Fetched HackerNews posts:")

    for p in posts:
        print("-", p["title"])

    save_posts(posts)

    print("\nSaved to data/trends.json")
