import time
import json
import re
import requests
from core.config import settings
from core.database import db
# Mengimpor daftar model dari modul core
from core.models import MODEL_LIST 

def fetch_top_opportunities(limit=5):
    """Mengambil ide dengan skor tertinggi yang belum memiliki blueprint."""
    # Menggunakan sorting DESC agar ide paling potensial dikerjakan lebih dulu
    query = f"opportunity_score=is.not.null&startup_name=is.null&order=opportunity_score.desc&limit={limit}"
    return db.fetch_records("ideas", query)

def call_openrouter(prompt):
    """Memanggil OpenRouter dengan sistem fallback model dari core.models."""
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
            # Gunakan timeout 60 detik agar tidak menghambat pipeline jika satu model lambat
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ Model {model} mengembalikan status: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Koneksi ke {model} gagal: {e}")
            continue
    return None

def main():
    print("=== AI Startup Factory: Blueprint Generator ===")
    
    # Ambil ide-ide yang sudah memiliki skor dari Ranker Agent
    rows = fetch_top_opportunities()

    if not rows:
        print("ℹ️ Tidak ada ide yang siap dirancang menjadi startup (skor kosong atau sudah diproses).")
        return

    print(f"🎯 Menemukan {len(rows)} peluang untuk dieksekusi.")

    for row in rows:
        problem = row.get("problem")
        print(f"\n🚀 Merancang konsep startup untuk: {problem[:70]}...")

        prompt = f"""
        Act as a Venture Builder. Create a high-potential startup concept for this problem:
        "{problem}"

        Return STRICT JSON format:
        {{
            "startup_name": "String (Creative name)",
            "pitch": "String (Elevator pitch)",
            "mvp_features": ["List of core features"],
            "tech_stack": ["Recommended languages, DB, and AI models"],
            "go_to_market": "String (Initial traction strategy)"
        }}
        """

        raw_response = call_openrouter(prompt)
        if not raw_response:
            print(f"❌ Gagal mendapatkan respon AI untuk ID: {row['id']}")
            continue

        try:
            # Membersihkan tag markdown jika AI menyertakannya dalam output
            clean_json = re.sub(r"```json\s?|\s?```", "", raw_response).strip()
            blueprint = json.loads(clean_json)

            # Update ke database menggunakan utilitas core.database
            success = db.update_record("ideas", row["id"], {
                "startup_name": blueprint.get("startup_name"),
                "startup_pitch": blueprint.get("pitch"),
                "mvp_spec": blueprint.get("mvp_features"), # Kolom JSONB
                "tech_stack": blueprint.get("tech_stack"), # Kolom JSONB
                "gtm_plan": blueprint.get("go_to_market")
            })

            if success:
                print(f"✅ Blueprint disimpan: {blueprint.get('startup_name')}")
            
            # Anti-spam delay
            time.sleep(1.5)

        except Exception as e:
            print(f"❌ Kesalahan pemrosesan data: {e}")

if __name__ == "__main__":
    main()
