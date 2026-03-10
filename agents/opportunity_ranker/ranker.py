import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


def load_ideas():

    url = f"{SUPABASE_URL}/rest/v1/ideas?opportunity_score=is.null&select=*"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    r = requests.get(url, headers=headers)

    return r.json()


def calculate_score(idea):

    trend = idea.get("trend_strength") or 0
    success = idea.get("success_probability") or 0
    score = idea.get("score") or 0

    opportunity_score = (trend * 2) + success + score

    return opportunity_score


def update_score(id,score):

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{id}"

    payload = {
        "opportunity_score":score
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":"application/json"
    }

    r = requests.patch(url,json=payload,headers=headers)

    print("Updated:",id,"score:",score)


def main():

    ideas = load_ideas()

    if not ideas:
        print("No ideas to score")
        return

    for idea in ideas:

        score = calculate_score(idea)

        update_score(
            idea["id"],
            score
        )


if __name__ == "__main__":
    main()
