# agents/opportunity_discovery/ranker.py
import os
# Import core infrastructure
from core.config import settings
from core.database import db

def load_ideas_needing_rank():
    """Retrieves ideas that have basic analysis but haven't been ranked yet."""
    # We look for ideas that have trend analysis but no final opportunity_score
    query = "opportunity_score=is.null&trend_strength=not.is.null&select=*"
    return db.fetch_records("ideas", query)

def calculate_weighted_rank(idea):
    """
    Calculates final Opportunity Score using weighted multi-factor analysis.
    Formula emphasizes Trends and Gap potential.
    """
    # 1. Trend Strength (Base: 1-10) -> Weight: 40%
    trend = float(idea.get("trend_strength") or 0)
    
    # 2. Success Probability (Base: 1-10) -> Weight: 20%
    success = float(idea.get("success_probability") or 0)
    
    # 3. Gap Score (Base: 0-100 from gap_detector) -> Weight: 40%
    # We normalize this to 1-10 scale
    gap_score = float(idea.get("opportunity_gap_score") or 0) / 10
    
    # Final Formula: (Trend * 4) + (Gap * 4) + (Success * 2)
    # Result scale: 0 - 100
    final_score = (trend * 4) + (gap_score * 4) + (success * 2)
    
    return round(final_score, 2)

def save_final_rank(idea_id, score):
    """Saves the final calculated score to the database."""
    payload = {
        "opportunity_score": score
    }
    return db.update_record("ideas", idea_id, payload)

def main():
    print("=== AI Startup Factory: Final Opportunity Ranker ===")
    
    # 1. Load Ideas
    ideas = load_ideas_needing_rank()
    
    if not ideas:
        print("✅ No new ideas found for ranking.")
        return

    print(f"📡 Ranking {len(ideas)} ideas for prioritization...")
    
    ranked_count = 0
    for idea in ideas:
        idea_id = idea.get("id")
        
        # 2. Calculation
        final_score = calculate_weighted_rank(idea)
        
        # 3. Sync to Database
        if save_final_rank(idea_id, final_score):
            print(f"⭐ ID {idea_id} Ranked: {final_score}/100")
            ranked_count += 1
        else:
            print(f"❌ Failed to update rank for ID: {idea_id}")

    print(f"\n=== Ranking Complete: {ranked_count} ideas prioritized. ===")

if __name__ == "__main__":
    main()
