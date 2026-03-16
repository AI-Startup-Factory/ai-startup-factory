import sys
import importlib
import time
from pathlib import Path
# Import infrastruktur core
from core.config import settings
from core.database import db

# Inisialisasi Path untuk dynamic importing
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Schema safe fields
VALID_FIELDS = {"source", "title", "url", "created_at", "content"}

def sanitize_signal(signal):
    """Membersihkan payload signal agar sesuai dengan skema DB."""
    return {k: v for k, v in signal.items() if k in VALID_FIELDS and v}

def is_new_signal(url):
    """Mengecek apakah URL signal sudah pernah diproses sebelumnya."""
    # Menggunakan db wrapper untuk cek keberadaan record
    result = db.fetch_records("signals", f"url=eq.{url}&select=id&limit=1")
    return len(result) == 0

def save_signal(signal):
    """Validasi, de-duplikasi, dan simpan signal ke database."""
    clean_data = sanitize_signal(signal)
    
    if "url" not in clean_data or "title" not in clean_data:
        return False

    if not is_new_signal(clean_data["url"]):
        print(f"⏩ Duplicate skipped: {clean_data['url']}")
        return False

    # Insert ke tabel signals
    # Default 'processed' = False agar bisa diambil oleh generator.py nanti
    clean_data["processed"] = False 
    
    success = db.insert_record("signals", clean_data)
    if success:
        print(f"✅ Ingested: {clean_data['title'][:60]}...")
    return success

def load_data_sources():
    """Mencari dan memuat modul scraper secara dinamis dari folder data_sources."""
    modules = []
    source_dir = ROOT_DIR / "agents" / "data_sources"
    
    if not source_dir.exists():
        print(f"⚠️ Source directory not found: {source_dir}")
        return []

    for file in source_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
            
        module_name = f"agents.data_sources.{file.stem}"
        try:
            # Import modul secara dinamis
            module = importlib.import_module(module_name)
            if hasattr(module, "fetch"):
                modules.append(module)
            else:
                print(f"⚠️ Skipped {file.name}: No fetch() function found.")
        except Exception as e:
            print(f"❌ Failed to load source {module_name}: {e}")
            
    return modules

def main():
    print("=== [AGENT] Global Trend Scanner ===")
    
    sources = load_data_sources()
    print(f"📡 Found {len(sources)} active data sources.")

    total_new_signals = 0

    for source in sources:
        source_name = source.__name__.split('.')[-1]
        print(f"\n🔄 Running source: {source_name.upper()}")
        
        try:
            # Eksekusi fungsi fetch() dari masing-masing scraper
            signals = source.fetch()
            
            if not signals:
                print(f"📭 No signals found for {source_name}")
                continue

            print(f"📥 Fetched {len(signals)} items. Processing...")
            
            for s in signals:
                if save_signal(s):
                    total_new_signals += 1
                    
        except Exception as e:
            print(f"❌ Error in source {source_name}: {e}")

    print(f"\n=== Scanning Finished: {total_new_signals} new signals added to factory ===")

if __name__ == "__main__":
    main()
