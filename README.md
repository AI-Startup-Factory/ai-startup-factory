# 🚀 AI Startup Factory (v2.0)

**AI Startup Factory** adalah ekosistem otonom yang dirancang untuk memindai tren global, mengeksplorasi celah pasar, dan membangun konsep startup siap eksekusi secara otomatis. Sistem ini bekerja 24/7 menggunakan rangkaian agen AI modular yang terintegrasi dengan GitHub Actions dan Supabase.

---

## 🏗️ Arsitektur & Alur Kerja

Sistem ini mengikuti prinsip **Modularization** dan **Separation of Concerns (SoC)**, di mana setiap agen memiliki tanggung jawab spesifik dalam satu jalur produksi:

1.  **Ingestion**: `Trend Scanner` memicu berbagai plugin di `data_sources` untuk mengumpulkan sinyal mentah.
2.  **Synthesis**: `Idea Generator` & `Problem Extractor` mengubah sinyal menjadi entitas bisnis terstruktur.
3.  **Intelligence**: `Embedding Agent` & `Deduplicator` memastikan data unik dan memiliki representasi vektor untuk analisis semantik.
4.  **Discovery**: `Clusterer` & `Gap Detector` menemukan pola dan celah peluang pasar yang belum jenuh.
5.  **Evaluation**: `Opportunity Scorer` (VC Mode) & `Ranker` memberikan penilaian objektif dan urutan prioritas.
6.  **Realization**: `Blueprint Generator` & `Landing Page Gen` menciptakan rencana teknis dan aset visual pemasaran.

---

## 📂 Struktur Proyek

```text
├── .github/workflows/       # Automasi Pipeline (Daily, Debug, Manual)
├── core/                    # Infrastruktur Inti (Config & DB Wrapper)
├── agents/
│   ├── data_sources/        # Plugin kolektor data (ArXiv, Reddit, HN, dll)
│   ├── trend_scanner/       # Orchestrator untuk menjalankan semua data_sources
│   ├── idea_generator/      # Mesin pembuat benih ide awal
│   ├── problem_extractor/   # Strukturisasi data (Problem/Solution/Audience)
│   ├── embedding_agent/     # Pemrosesan vektor (Sentence-Transformers)
│   ├── semantic_deduplicator/# Pembersihan duplikasi berbasis kemiripan makna
│   ├── clusterer/           # Pengelompokan ide berdasarkan topik
│   ├── market_analyzer/     # Analisis tren dan ukuran pasar
│   ├── opportunity_discovery/ # Analisis celah vektor (Gap Analysis)
│   ├── opportunity_gap_detector/ # Kalkulasi skor densitas & momentum
│   ├── opportunity_scorer/  # Penilaian kualitatif gaya Venture Capital
│   ├── opportunity_ranker/  # Agregasi skor final & pembobotan
│   ├── startup_generator/   # Pembuat blueprint teknis & spesifikasi MVP
│   ├── trend_momentum/      # Validasi eksternal (HackerNews & GitHub Stars)
│   └── web_generator/       # Pembuat Landing Page otomatis (Tailwind CSS)
├── requirements.txt         # Dependensi Python
└── README.md                # Dokumentasi Proyek
