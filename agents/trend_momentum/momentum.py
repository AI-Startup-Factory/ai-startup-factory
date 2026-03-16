import math
import time
import re
import requests
# Import infrastruktur core
from core.config import settings
from core.database import db

# Konfigurasi API Eksternal
HN_API = "https://hn.algolia.com/api/v1/search"
GITHUB_API = "https://api.github.com/search/repositories"

def fetch_ideas_for_momentum():
    """Mengambil ide yang perlu divalidasi momentumnya."""
    # Kita bisa membatasi hanya untuk ide yang belum punya momentum_score
    query = "select=id,problem&momentum_score=is.null&limit=20"
    return db.fetch_records("ideas", query)

def extract_keywords(text):
    """Membersihkan teks dan mengambil 3 kata kunci utama untuk pencarian."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = text.split()
    
    stopwords = {
        "the","and","for","with","that","this","from","into","using","build",
        "system","platform","software","current","existing","methods","approach",
        "model","models","data","based","analysis","problem","solution","applications"
    }

    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    return " ".join(keywords[:3])

def get_hn_score(query):
    """Mencari popularitas topik di HackerNews (Points + Comments)."""
    try:
        params = {"query": query, "tags": "story", "hitsPerPage": 10}
        r = requests.get(HN_API, params=params, timeout=20)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            return sum(h.get("points", 0) + h.get("num_comments", 0) for h in hits)
    except Exception as e:
        print(f"⚠️ HN Search Error: {e}")
    return 0

def get_github_score(query):
    """Mencari aktivitas kode di GitHub (Stars + Forks)."""
    # Pastikan AI_STARTUP_TOKEN ada di .env atau GitHub Secrets
    github_token = getattr(settings, "AI_STARTUP_TOKEN", None)
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 5}
        r = requests.get(GITHUB_API, headers=headers, params=params, timeout=20)
        if r.status_code == 200:
            items = r.json().get("items", [])
            return sum(item.get("stargazers_count", 0) + item.get("forks_count", 0) for item in items)
    except Exception as e:
        print(f"⚠️ GitHub Search Error: {e}")
    return 0

def normalize_velocity(momentum):
    """Mengonversi skor logaritmik momentum ke skala velocity 1-10."""
    thresholds = [
        (2000, 10), (1000, 9), (500, 8), (200, 7), (100, 6),
        (50, 5), (20, 4), (10, 3), (5, 2)
    ]
    for limit, val in thresholds:
        if momentum > limit: return val
    return 1

def main():
    print("=== [AGENT] Trend & Momentum Analyzer ===")
    ideas = fetch_ideas_for_momentum()
    
    if not ideas:
        print("✅ Semua ide sudah memiliki skor momentum.")
        return

    for idea in ideas:
        idea_id = idea["id"]
        problem = idea["problem"]
        
        keywords = extract_keywords(problem)
        print(f"\n🔍 Querying momentum for: '{keywords}'")

        hn = get_hn_score(keywords)
        gh = get_github_score(keywords)

        # Kalkulasi Momentum (Logaritmik agar angka jutaan tidak merusak skala)
        # Log1p(x) = log(1+x)
        momentum = int((math.log1p(hn) * 3) + (math.log1p(gh) * 2))
        velocity = normalize_velocity(momentum)

        # Update DB
        payload = {
            "hn_score": hn,
            "github_score": gh,
            "momentum_score": momentum,
            "trend_velocity": velocity
        }
        
        if db.update_record("ideas", idea_id, payload):
            print(f"📈 Updated ID {idea_id}: Momentum={momentum}, Velocity={velocity} (HN:{hn}, GH:{gh})")
        
        time.sleep(1) # Etika API

if __name__ == "__main__":
    main()
