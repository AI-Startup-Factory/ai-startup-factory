import math
# Import core infrastructure
from core.config import settings
from core.database import db

def fetch_ideas_for_scoring():
    """Retrieves all ideas with necessary metadata for opportunity scoring."""
    query = "select=id,cluster_id,cluster_size,trend_strength,market_size,competition"
    return db.fetch_records("ideas", query)

def normalize_market_size(value):
    """Translates market size descriptions into a numerical weight (0.0 - 1.0)."""
    if not value: return 0.5
    v = str(value).lower()
    if "trillion" in v: return 1.0
    if "billion" in v: return 0.8
    if "million" in v: return 0.5
    return 0.3

def normalize_competition(value):
    """Translates competition levels into an inverse weight (Low = High Opportunity)."""
    if not value: return 0.5
    v = str(value).lower()
    if "high" in v: return 0.2
    if "medium" in v: return 0.5
    if "low" in v: return 0.8
    return 0.5

def calculate_mean(data_list):
    """Calculates the average of a list, returns 0 if list is empty."""
    if not data_list: return 0
    return sum(data_list) / len(data_list)

def update_opportunity_metrics(row_id, density, momentum, score):
    """Persists calculated scores back to the database."""
    payload = {
        "cluster_density": float(density),
        "cluster_momentum": float(momentum),
        "cluster_opportunity_score": float(score),
        "opportunity_gap_score": int(score * 100) # Percentage-based score for ranking
    }
    return db.update_record("ideas", row_id, payload)

def main():
    print("=== AI Startup Factory: Opportunity Gap Detector ===")
    
    # 1. Fetch data
    ideas = fetch_ideas_for_scoring()
    if not ideas:
        print("❌ No ideas found to analyze. Ensure Clusterer and Analyzer have run.")
        return

    # 2. Grouping by Cluster
    clusters = {}
    for i in ideas:
        cid = i.get("cluster_id")
        if cid is None: continue
        if cid not in clusters: clusters[cid] = []
        clusters[cid].append(i)

    print(f"📡 Analyzing {len(clusters)} clusters...")

    # 3. Cluster Scoring Logic
    cluster_metrics = {}
    for cid, rows in clusters.items():
        size = len(rows)
        
        # Density: High density (many ideas) reduces 'gap' opportunity
        # Formula: Cap at 20 ideas for max density
        density = min(1.0, size / 20)

        # Momentum: Based on AI-generated trend_strength
        trend_values = [float(r.get("trend_strength") or 3) for r in rows]
        momentum = calculate_mean(trend_values) / 10 # Normalize 1-10 scale to 0.1-1.0

        # Market & Competition Weights
        market_scores = [normalize_market_size(r.get("market_size")) for r in rows]
        market_score = calculate_mean(market_scores)

        comp_scores = [normalize_competition(r.get("competition")) for r in rows]
        competition_score = calculate_mean(comp_scores)

        # FINAL FORMULA (Weighted Average)
        # 35% Gap (1-Density), 25% Trend, 25% Market Size, 15% Low Competition
        opportunity_score = (
            (1 - density) * 0.35 +
            momentum * 0.25 +
            market_score * 0.25 +
            competition_score * 0.15
        )

        cluster_metrics[cid] = {
            "density": density,
            "momentum": momentum,
            "score": opportunity_score
        }

    # 4. Batch Update Results
    print(f"💾 Syncing opportunity scores to database...")
    success_count = 0
    for i in ideas:
        cid = i.get("cluster_id")
        if cid not in cluster_metrics: continue
        
        metrics = cluster_metrics[cid]
        if update_opportunity_metrics(i["id"], metrics["density"], metrics["momentum"], metrics["score"]):
            success_count += 1

    print(f"✅ Scoring complete. {success_count} ideas updated with Opportunity Scores.")

if __name__ == "__main__":
    main()
