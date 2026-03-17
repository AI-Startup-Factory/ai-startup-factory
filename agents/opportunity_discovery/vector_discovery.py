import json
import random
import requests
import re
from core.config import settings
from core.database import db

def fetch_clustered_ideas():
    """Retrieves all ideas that have been assigned to a cluster."""
    # Gunakan format is.not.null yang lebih stabil
    query = "select=id,problem,cluster_id&cluster_id=is.not.null"
    return db.fetch_records("ideas", query)

def group_by_cluster(rows):
    """Groups problem statements by their cluster ID for analysis."""
    clusters = {}
    for r in rows:
        cid = r.get("cluster_id")
        if cid is None: continue
        
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(r["problem"])
    return clusters

def call_discovery_ai(cluster_id, problems):
    """Calls AI with fallback mechanism."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-startup-factory"
    }
    
    context_text = "\n- ".join(problems)
    prompt = f"""
    You are a startup opportunity analyst. 
    The following problems belong to the same technology/market cluster (Cluster ID: {cluster_id}).
    
    EXISTING PROBLEMS:
    - {context_text}
    
    TASK:
    Identify 2-3 'Missing Adjacent Opportunities' or Gaps. 
    These should be logical extensions or underserved niches that fit in this cluster.
    
    Return ONLY a JSON object:
    {{
      "gaps": [
        {{
          "title": "Short title",
          "description": "Why this is a missing opportunity"
        }}
      ]
    }}
    """

    # Gunakan getattr agar tidak AttributeError
    static_models = getattr(settings, "MODELS", ["google/gemini-2.0-flash-exp:free"])
    all_models = static_models.copy()
    random.shuffle(all_models)

    for model in all_models:
        print(f"🔍 Analyzing gaps in Cluster {cluster_id} using {model}...")
        try:
            r = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }, timeout=60)
            
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                # Bersihkan markdown jika ada
                clean_content = re.sub(r"```json\s?|\s?```", "", content).strip()
                return clean_content
        except Exception as e:
            print(f"⚠️ Model {model} failed: {e}")
            continue
    return None

def save_gap_as_signal(gap):
    """Saves the identified gap back into the signals table using core database."""
    payload = {
        "title": gap.get("title"),
        "content": gap.get("description"),
        "processed": False,
        "source": "vector_discovery_agent"
    }
    # MENGGUNAKAN WRAPPER DATABASE CORE
    return db.insert_record("signals", payload)

def main():
    print("=== AI Startup Factory: Vector Gap Discovery ===")
    
    rows = fetch_clustered_ideas()
    if not rows:
        print("✅ No clustered ideas found for gap analysis.")
        return

    clusters = group_by_cluster(rows)
    total_gaps_found = 0

    for cid, problems in clusters.items():
        # Fokus pada cluster yang sudah punya cukup konteks
        if len(problems) < 2:
            continue

        print(f"📡 Processing Cluster {cid} ({len(problems)} ideas)...")
        ai_response = call_discovery_ai(cid, problems)
        
        if not ai_response:
            continue

        try:
            data = json.loads(ai_response)
            gaps = data.get("gaps", [])
            
            for gap in gaps:
                if save_gap_as_signal(gap):
                    print(f"✨ New Gap Discovered: {gap.get('title')}")
                    total_gaps_found += 1
        except Exception as e:
            print(f"❌ Error parsing gaps for cluster {cid}: {e}")

    print(f"\n=== Discovery Complete: {total_gaps_found} new signals injected into the loop. ===")

if __name__ == "__main__":
    main()
