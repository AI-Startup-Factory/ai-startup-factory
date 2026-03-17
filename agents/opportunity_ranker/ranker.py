from core.config import settings
from core.database import db

def main():
    print("=== [AGENT] Opportunity Ranker ===")
    
    # PERBAIKAN: Cari ide yang sudah di-cluster (cluster_id not null) 
    # tapi opportunity_score-nya masih kosong (null)
    query = "cluster_id=is.not.null&opportunity_score=is.null&select=*"
    ideas = db.fetch_records("ideas", query)
    
    if not ideas:
        print("✅ Tidak ada ide baru yang siap diranking.")
        return

    print(f"📊 Meranking {len(ideas)} ide...")

    for idea in ideas:
        # Kita gunakan bobot dari berbagai skor yang dihasilkan agen sebelumnya
        # Jika nilai null, kita gunakan default 0
        market_score = float(idea.get("market_score") or 0)
        trend_score = float(idea.get("trend_score") or 0)
        gap_score = float(idea.get("opportunity_gap_score") or 0)
        
        # Success probability biasanya skala 1-10 atau 1-100, pastikan konsisten
        success_prob = float(idea.get("success_probability") or 0)

        # RUMUS RANKING (Bisa disesuaikan bobotnya):
        # 30% Market + 30% Trend + 30% Gap + 10% Success Probability
        final_priority = (market_score * 0.3) + (trend_score * 0.3) + (gap_score * 0.3) + (success_prob * 0.1)

        # Jika hasil 0 (mungkin karena agen market belum jalan), kita beri skor default kecil 
        # agar tetap bisa masuk ke generator
        if final_priority == 0:
            final_priority = (float(idea.get("trend_strength") or 0))

        # Update skor prioritas final ke kolom opportunity_score
        db.update_record("ideas", idea["id"], {
            "opportunity_score": int(final_priority)
        })
        print(f"⭐ ID {idea['id']} -> Calculated Score: {int(final_priority)}")

    print("✅ Ranking dan Prioritasi Selesai.")

if __name__ == "__main__":
    main()
