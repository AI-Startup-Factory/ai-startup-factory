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
You are a startup idea generator.

From the following tech headlines, generate 5 startup ideas.

Headlines:
{headlines}

Return concise ideas.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-oss-120b:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    data = response.json()

print("\nFULL API RESPONSE:")
print(data)

ideas = data["choices"][0]["message"]["content"]

    return ideas


if __name__ == "__main__":

    posts = load_posts()

    ideas = generate_ideas(posts)

    print("\nGenerated Ideas:\n")
    print(ideas)
