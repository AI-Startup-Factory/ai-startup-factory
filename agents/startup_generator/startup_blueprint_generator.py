import time
import json
import re
import requests
from core.config import settings
from core.database import db

# List model untuk rotasi anti rate-limit
MODEL_LIST = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-72b-chat:free"
]

def fetch_top_opportunities(limit=5):
    """Mengambil ide dengan skor tertinggi yang belum memiliki blueprint."""
    # Menggunakan sorting desc agar ide paling potensial dikerjakan duluan
    query = f"opportunity_score=is.not.null&startup_name=is.null&order=opportunity_score.desc&limit={limit}"
    return db.fetch_records("ideas", query)

def call_openrouter(prompt):
    """Memanggil OpenRouter dengan sistem fallback model."""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }

    for model in MODEL_LIST:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        try:
            # Menggunakan timeout agar tidak menggantung jika model lambat
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                             headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"⚠️ Model {model} gagal: {e}")
            continue
    return None

def main():
    print("=== AI Startup Factory: Blueprint Generator ===")
    
    # Ambil ide-ide yang sudah diranking oleh Ranker Agent
    rows = fetch_top_opportunities()

    if not rows:
        print("ℹ️ Tidak ada ide yang siap dibuatkan blueprint.")
        return

    for row in rows:
        problem = row.get("problem")
        print(f"\n🚀 Merancang Startup untuk: {problem[:60]}...")

        prompt = f"""
        Act as a Venture Builder. Create a startup concept for this problem:
        {problem}

        Return STRICT JSON:
        {{
            "startup_name": "Name",
            "pitch": "Elevator pitch",
            "mvp_features": ["feature1", "feature2"],
            "tech_stack": ["tech1", "tech2"],
            "go_to_market": "Marketing strategy"
        }}
        """

        raw_response = call_openrouter(prompt)
        if not raw_response: continue

        try:
            # Clean markdown jika ada
            clean_json = re.sub(r"```json\s?|\s?```", "", raw_response).strip()
            blueprint = json.loads(clean_json)

            # Update ke database menggunakan skema kolom yang sudah divalidasi
            success = db.update_record("ideas", row["id"], {
                "startup_name": blueprint.get("startup_name"),
                "startup_pitch": blueprint.get("pitch"),
                "mvp_spec": blueprint.get("mvp_features"), # Tipe JSONB
                "tech_stack": blueprint.get("tech_stack"), # Tipe JSONB
                "gtm_plan": blueprint.get("go_to_market")
            })

            if success:
                print(f"✅ Blueprint sukses disimpan: {blueprint.get('startup_name')}")
            
            # Delay kecil untuk menghindari rate limit API
            time.sleep(1)

        except Exception as e:
            print(f"❌ Gagal memproses JSON: {e}")

if __name__ == "__main__":
    main()
