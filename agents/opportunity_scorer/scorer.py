import os
import requests
import json
import time
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)"

# ===================================
# FALLBACK MODEL LIST
# ===================================
MODEL_LIST = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "qwen/qwen3-4b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-mini:free",
    "z-ai/glm-4.5-air:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ===================================
# HELPER: CLEAN SCORE (Avoid 22P02 Error)
# ===================================
def clean_int_score(val):
    """Mengonversi nilai apapun dari AI menjadi Integer yang valid untuk DB."""
    try:
        if val is None: return 0
        # Konversi ke float dulu (untuk handle "8.5"), lalu bulatkan
        return int(round(float(val)))
    except (ValueError, TypeError):
        return 0

# ===================================
# FETCH IDEAS
# ===================================
def fetch_ideas():
    # Mengambil ide yang belum memiliki opportunity_score
    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem&opportunity_score=is.null&limit=25"
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []
    except:
        return []

# ===================================
# CALL AI WITH FALLBACK & CLEANING
# ===================================
def call_ai(prompt):
    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "[https://github.com/ai-startup-factory](https://github.com/ai-startup-factory)",
        "X-Title": "AI Startup Factory Scorer"
    }

    for model in MODEL_LIST:
        print(f"Trying model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            r = requests.post(OPENROUTER_URL, headers=headers_ai, json=payload, timeout=60)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                if content: return content
            elif r.status_code == 429:
                continue
        except:
            continue
    return None

# ===================================
# SCORE PROBLEM
# ===================================
def score_problem(problem):
    prompt = f"""
    You are a venture capital analyst. Evaluate this startup opportunity.
    Problem: {problem}
    Score each category from 0 to 10.
    Return STRICT JSON format:
    {{
      "trend": number,
      "market": number,
      "competition": number,
      "feasibility": number,
      "founder_fit": number
    }}
    """
    response = call_ai(prompt)
    if not response: return None

    try:
        # Bersihkan markdown jika ada
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return None

# ===================================
# CALCULATE FINAL SCORE
# ===================================
def calculate_score(scores):
    # Menggunakan clean_int_score untuk memastikan keamanan data
    trend = clean_int_score(scores.get("trend"))
    market = clean_int_score(scores.get("market"))
    competition = clean_int_score(scores.get("competition"))
    feasibility = clean_int_score(scores.get("feasibility"))
    founder = clean_int_score(scores.get("founder_fit"))

    # Bobot penilaian
    weighted_sum = (
        0.30 * trend +
        0.25 * market +
        0.20 * competition +
        0.15 * feasibility +
        0.10 * founder
    )
    # Kembalikan sebagai integer (0-100) untuk kolom opportunity_score
    return int(round(weighted_sum * 10))

# ===================================
# UPDATE DATABASE
# ===================================
def update_row(row_id, scores, final_score):
    payload = {
        "trend_score": clean_int_score(scores.get("trend")),
        "market_score": clean_int_score(scores.get("market")),
        "competition_score": clean_int_score(scores.get("competition")),
        "feasibility_score": clean_int_score(scores.get("feasibility")),
        "founder_fit_score": clean_int_score(scores.get("founder_fit")),
        "opportunity_score": final_score # Pastikan ini integer
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"
    try:
        r = requests.patch(url, headers=headers, json=payload)
        if r.status_code in [200, 204]:
            print(f"Successfully updated ID: {row_id} with score {final_score}")
        else:
            print(f"Update failed for {row_id}: {r.text}")
    except Exception as e:
        print(f"Connection error during update: {e}")

# ===================================
# MAIN
# ===================================
def main():
    print("=== AI Startup Factory: Opportunity Scorer ===")
    rows = fetch_ideas()

    if not rows:
        print("No new ideas found to score.")
        return

    print(f"Found {len(rows)} ideas to process.")

    for row in rows:
        problem = row["problem"]
        print(f"\nScoring: {problem[:70]}...")

        scores = score_problem(problem)
        if not scores:
            print("Skipping due to AI failure.")
            continue

        final = calculate_score(scores)
        update_row(row["id"], scores, final)
        
        # Jeda singkat untuk menghindari rate limit database
        time.sleep(1)

if __name__ == "__main__":
    main()
