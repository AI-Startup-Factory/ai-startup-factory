import os
import requests
import json
import time
import re
from pathlib import Path

# =====================================
# CONFIG & ENV (Prinsip 3 & 9)
# =====================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

BATCH_SIZE = 20

# Daftar model free terbaru untuk redundansi (Prinsip 16)
MODEL_LIST = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-12b-it:free",
    "qwen/qwen-turbo-latest:free"
]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# =====================================
# FETCH DATA (Alignment dengan Skema Baru)
# =====================================
def fetch_tasks():
    # Karena kolom 'idea' tidak ada, kita mencari record yang 'solution'-nya masih kosong 
    # untuk diproses berdasarkan input di kolom 'problem'
    url = f"{SUPABASE_URL}/rest/v1/ideas?solution=is.null&select=id,problem&limit={BATCH_SIZE}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"Fetch error: {r.status_code} - {r.text}")
            return []
        return r.json()
    except Exception as e:
        print(f"Connection error during fetch: {e}")
        return []

# =====================================
# CALL AI WITH FALLBACK (Prinsip 16)
# =====================================
def call_ai(prompt):
    headers_ai = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory", 
        "X-Title": "AI Startup Factory Extractor"
    }

    for model in MODEL_LIST:
        print(f"Attempting extraction with: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, # Rendah agar JSON lebih stabil
            "response_format": {"type": "json_object"}
        }

        try:
            r = requests.post(OPENROUTER_URL, headers=headers_ai, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                print("Rate limited, skipping model...")
                continue
        except Exception as e:
            print(f"Model {model} failed: {e}")
        
        time.sleep(1)
    return None

# =====================================
# PARSE & UPDATE (Prinsip 2: SoC)
# =====================================
def parse_json(text):
    try:
        text = re.sub(r"```json\s?|\s?```", "", text).strip()
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: return None
    return None

def update_database(idea_id, data):
    # Mapping data ke kolom yang benar-benar ada di tabel ideas Anda
    payload = {
        "problem": data.get("problem"),
        "solution": data.get("solution"),
        "audience": data.get("audience"),
        "market": data.get("market", "Unknown")
    }

    url = f"{SUPABASE_URL}/rest/v1/ideas?id=eq.{idea_id}"
    try:
        r = requests.patch(url, json=payload, headers=headers)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"Update error for {idea_id}: {e}")
        return False

# =====================================
# MAIN RUNNER
# =====================================
def main():
    print("=== AI Startup Factory: Problem Extractor ===")
    
    tasks = fetch_tasks()
    if not tasks:
        print("No new tasks found in 'ideas' table.")
        return

    print(f"Processing {len(tasks)} items...")

    for item in tasks:
        # Menggunakan kolom 'problem' sebagai basis deskripsi yang akan diperkaya
        raw_text = item.get("problem", "") 
        if not raw_text:
            continue

        prompt = f"""
        Act as a business analyst. Analyze this startup idea and extract structured details.
        
        Raw Input: {raw_text}

        Return ONLY a JSON object with this exact structure:
        {{
            "problem": "detailed problem statement",
            "solution": "detailed solution description",
            "audience": "target user persona",
            "market": "industry category"
        }}
        """

        ai_response = call_ai(prompt)
        if not ai_response:
            continue

        parsed_data = parse_json(ai_response)
        if parsed_data:
            success = update_database(item["id"], parsed_data)
            if success:
                print(f"Successfully updated ID: {item['id']}")
            else:
                print(f"Failed to update ID: {item['id']}")
        
        time.sleep(1) # Etika API

if __name__ == "__main__":
    main()
