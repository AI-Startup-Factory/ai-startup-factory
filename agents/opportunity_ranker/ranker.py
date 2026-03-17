from core.config import settings
from core.database import db

def main():
    print("=== AI Startup Factory: Opportunity Ranker ===")
    
    # Menarik ide yang sudah di-cluster namun belum memiliki skor final
    # Menggunakan modul core.database agar tidak ada hardcode URL/Key
    query = "cluster_id=is.not.null&opportunity_score=is.null&select=*"
    ideas = db.fetch_records("ideas", query)
    
    if not ideas:
        print("✅ Tidak ada ide baru yang perlu diranking.")
        return

    print(f"📊 Menghitung skor untuk {len(ideas)} ide...")

    for idea in ideas:
        # Mengambil metrik kualitatif dengan fallback ke 0
        market_score = float(idea.get("market_score") or 0)
        trend_score = float(idea.get("trend_score") or 0)
        gap_score = float(idea.get("opportunity_gap_score") or 0)
        success_prob = float(idea.get("success_probability") or 0)

        # RUMUS: 30% Market, 30% Trend, 30% Gap, 10% Success Prob
        final_priority = (market_score * 0.3) + (trend_score * 0.3) + (gap_score * 0.3) + (success_prob * 0.1)

        # Fallback jika skor nol: gunakan trend_strength dasar
        if final_priority == 0:
            final_priority = float(idea.get("trend_strength") or 5)

        # Update ke kolom opportunity_score di Supabase
        payload = {"opportunity_score": int(final_priority)}
        if db.update_record("ideas", idea["id"], payload):
            print(f"⭐ ID {idea['id'][:8]}... -> Score: {int(final_priority)}")
        else:
            print(f"❌ Gagal memperbarui skor untuk ID: {idea['id']}")

    print("✅ Proses Ranking Selesai.")

if __name__ == "__main__":
    main()
