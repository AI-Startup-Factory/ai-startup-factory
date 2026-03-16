import math
from core.config import settings
from core.database import db

def fetch_ideas_for_gap():
    """Mengambil ide yang sudah diklaster untuk dihitung peluang celahnya."""
    query = "select=id,cluster_id,cluster_size,trend_strength,market_size,competition"
    return db.fetch_records("ideas", query)

def normalize_market(v):
    v = str(v).lower() if v else ""
    if "trillion" in v: return 1.0
    if "billion" in v: return 0.8
    if "million" in v: return 0.5
    return 0.3

def normalize_comp(v):
    v = str(v).lower() if v else ""
    if "low" in v: return 0.8
    if "medium" in v: return 0.5
    if "high" in v: return 0.2
    return 0.5

def main():
    print("=== [AGENT] Opportunity Gap Detector ===")
    ideas = fetch_ideas_for_gap()
    if not ideas:
        print("✅ Tidak ada data klaster untuk dianalisis.")
        return

    # Kelompokkan berdasarkan klaster
    clusters = {}
    for i in ideas:
        cid = i.get("cluster_id")
        if cid:
            if cid not in clusters: clusters[cid] = []
            clusters[cid].append(i)

    print(f"📡 Menganalisis {len(clusters)} klaster...")

    for cid, rows in clusters.items():
        size = len(rows)
        # Semakin padat klaster, semakin kecil peluang 'gap' (1 - density)
        density = min(1.0, size / 20)
        
        # Hitung rata-rata tren
        trends = [float(r.get("trend_strength") or 30) for r in rows]
        momentum = (sum(trends) / len(trends)) / 100

        # Skor rata-rata market dan kompetisi
        m_score = sum(normalize_market(r.get("market_size")) for r in rows) / size
        c_score = sum(normalize_comp(r.get("competition")) for r in rows) / size

        # Rumus Peluang: Bobot Gap(35%), Momentum(25%), Market(25%), Comp(15%)
        opp_score = ((1 - density) * 0.35) + (momentum * 0.25) + (m_score * 0.25) + (c_score * 0.15)

        # Update semua ide dalam klaster ini
        for r in rows:
            payload = {
                "cluster_density": float(density),
                "cluster_momentum": float(momentum),
                "cluster_opportunity_score": float(opp_score),
                "opportunity_gap_score": int(opp_score * 100)
            }
            db.update_record("ideas", r["id"], payload)
    
    print("✅ Analisis Gap Selesai.")

if __name__ == "__main__":
    main()
