from core.config import settings
from core.database import db

def main():
    print("=== [AGENT] Opportunity Ranker ===")
    # Ambil ide yang sudah memiliki skor kualitatif (opportunity_score)
    ideas = db.fetch_records("ideas", "opportunity_score=not.is.null&select=*")
    
    if not ideas:
        print("✅ Tidak ada ide yang siap diranking.")
        return

    print(f"📊 Meranking {len(ideas)} ide...")

    for idea in ideas:
        # Rumus Ranker: 40% dari Scorer AI, 40% dari Gap Detector, 20% Success Prob
        ai_score = float(idea.get("opportunity_score") or 0)
        gap_score = float(idea.get("opportunity_gap_score") or 0)
        success_prob = float(idea.get("success_probability") or 0) * 10

        final_priority = (ai_score * 0.4) + (gap_score * 0.4) + (success_prob * 0.2)

        # Update skor prioritas final
        db.update_record("ideas", idea["id"], {
            "opportunity_score": int(final_priority)
        })
        print(f"⭐ ID {idea['id']} -> Rank Score: {int(final_priority)}")

    print("✅ Ranking dan Prioritasi Selesai.")

if __name__ == "__main__":
    main()
