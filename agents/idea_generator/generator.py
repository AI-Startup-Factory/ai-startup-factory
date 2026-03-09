import requests
import os
from openai import OpenAI


def fetch_hackernews():
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    story_ids = requests.get(url).json()[:5]

    posts = []

    for sid in story_ids:
        story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json").json()
        if story and "title" in story:
            posts.append(story["title"])

    return posts


def generate_ideas(posts):

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
You are a startup idea generator.

Based on these tech news headlines:

{posts}

Identify possible problems users might have and generate 3 startup ideas.
Return short ideas only.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


if __name__ == "__main__":

    posts = fetch_hackernews()

    print("Headlines:")
    for p in posts:
        print("-", p)

    ideas = generate_ideas(posts)

    print("\nGenerated Startup Ideas:\n")
    print(ideas)
