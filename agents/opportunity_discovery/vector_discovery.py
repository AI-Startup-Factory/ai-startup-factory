import json
import random
import requests
# Import core infrastructure
from core.config import settings
from core.database import db

def fetch_clustered_ideas():
    """Retrieves all ideas that have been assigned to a cluster."""
    query = "select=id,problem,cluster_id&cluster_id=not.is.null"
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
    """Calls AI to identify missing gaps within a specific cluster."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    context_text = "\n- ".join(problems)
    prompt = f"""
    You are a startup opportunity analyst. 
    The following problems belong to the same technology/market cluster (Cluster ID: {cluster_id}).
    
    EXISTING PROBLEMS:
    - {context_text}
    
    TASK:
    Identify 2-3 'Missing Adjacent Opportunities' or Gaps. 
    These should be logical extensions or underserved niches that are NOT explicitly listed above but fit in this cluster.
    
    Return ONLY a JSON object with this structure:
    {{
      "gaps": [
        {{
          "title": "Short title for the gap",
          "description": "Why this is a missing opportunity"
        }}
      ]
    }}
    """

    # Use robust model fallback from core
    all_models = settings.MODELS.copy()
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
                return r.json()["choices"][0]["message"]["content"]
        except:
            continue
    return None

def save_gap_as_signal(gap):
    """Saves the identified gap back into the signals table for the next generation cycle."""
    url = f"{settings.SUPABASE_URL}/rest/v1/signals"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": gap.get("title"),
        "content": gap.get("description"),
        "processed": False,
        "source": "vector_discovery_agent"
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        return r.status_code in [200, 201, 204]
    except:
        return False

def main():
    print("=== AI Startup Factory: Vector Gap Discovery ===")
    
    # 1. Fetch and Group
    rows = fetch_clustered_ideas()
    if not rows:
        print("✅ No clustered ideas found. Run the Clusterer first.")
        return

    clusters = group_by_cluster(rows)
    total_gaps_found = 0

    # 2. Analyze Gaps per Cluster
    for cid, problems in clusters.items():
        # Only analyze mature clusters with enough data points
        if len(problems) < 3:
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
