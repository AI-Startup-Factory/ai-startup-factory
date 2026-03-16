import os
import requests
import json
import time
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ====================================
# PRIMARY MODEL LIST (ANTI RATE LIMIT)
# ====================================
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
    "Content-Type": "application/json"
}

# ====================================
# FETCH OPPORTUNITIES (THRESHOLD ADJUSTED)
# ====================================
def fetch_opportunities():
    # Menurunkan threshold ke 20 agar ide bernilai 21-25 masuk ke generator
    url = f"{SUPABASE_URL}/rest/v1/ideas?select=id,problem,opportunity_score&opportunity_score=gte.20&startup_name=is.null&limit=5"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print("Fetch error:", r.text)
            return []
        return r.json()
    except:
        return []

# ====================================
# CALL AI WITH FALLBACK
# ====================================
def call_ai(prompt):
    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    for model in MODEL_LIST:
        print("Trying model:", model)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }

        try:
            r = requests.post(OPENROUTER_URL, headers=headers_ai, json=payload, timeout=90)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            continue
        except:
            continue
    return None

# ====================================
# GENERATE STARTUP BLUEPRINT
# ====================================
def generate_startup(problem):
    prompt = f"""
You are a startup studio. Create a startup concept solving this problem.
Problem: {problem}

Return STRICT JSON format:
{{
"startup_name": "...",
"pitch": "...",
"mvp_features": ["f1", "f2", "f3"],
"tech_stack": ["fe", "be", "ai", "infra"],
"go_to_market": "..."
}}
"""
    response = call_ai(prompt)
    if not response: return None

    try:
        # Pembersihan tag markdown jika AI menyertakannya
        clean_json = re.sub(r"```json\s?|\s?```", "", response).strip()
        return json.loads(clean_json)
    except Exception as e:
        print("JSON parse error for response:", response[:100])
        return None

# ====================================
# UPDATE DATABASE
# ====================================
def update_row(row_id, blueprint):
    payload = {
        "startup_name": blueprint.get("startup_name", "Unnamed Startup"),
        "startup_pitch": blueprint.get("pitch", ""),
        "mvp_spec": blueprint.get("mvp_features", []),
        "tech_stack": blueprint.get("tech_stack", []),
        "gtm_plan": blueprint.get("go_to_market", "")
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{row_id}"
    r = requests.patch(url, headers=headers, json=payload)

    if r.status_code in [200, 204]:
        print(f"✅ Startup blueprint generated for ID: {row_id}")
    else:
        print(f"❌ Update failed: {r.text}")

# ====================================
# MAIN
# ====================================
def main():
    print("=== AI Startup Factory: Blueprint Generator ===")
    rows = fetch_opportunities()

    if not rows:
        print("No ideas found with score >= 20. Waiting for better opportunities.")
        return

    print(f"Found {len(rows)} opportunities to build.")

    for row in rows:
        problem = row["problem"]
        print(f"\nGenerating startup for: {problem[:70]}...")

        blueprint = generate_startup(problem)
        if not blueprint:
            continue

        update_row(row["id"], blueprint)
        time.sleep(2)

if __name__ == "__main__":
    main()
