import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def load_posts():
    with open("data/trends.json") as f:
        return json.load(f)


def generate_ideas(posts):

    headlines = [p["title"] for p in posts[:5]]

    print("Headlines:")
    for h in headlines:
        print("-", h)

    prompt = f"""
Generate 5 startup ideas based on these tech headlines.

Headlines:
{headlines}

Return ONLY the ideas.
No explanations.
No reasoning.
Just a numbered list.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemma-3-27b-it:free",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    )

    data = response.json()

    if "choices" not in data:
        print("\nAPI ERROR RESPONSE:")
        print(data)
        raise Exception("OpenRouter response missing 'choices'")

    ideas = data["choices"][0]["message"]["content"]

    return ideas


if __name__ == "__main__":

    posts = load_posts()

    ideas = generate_ideas(posts)

    print("\nGenerated Ideas:\n")
    print(ideas)
