import sys
import importlib
import time
from pathlib import Path
from urllib.parse import quote # Untuk mengamankan URL
from core.config import settings
from core.database import db

# Inisialisasi Path - Lebih robust untuk lingkungan GitHub Actions
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

VALID_FIELDS = {"source", "title", "url", "created_at", "content"}

def sanitize_signal(signal):
    """Membersihkan payload signal agar sesuai dengan skema DB."""
    clean = {k: v for k, v in signal.items() if k in VALID_FIELDS and v}
    # Pastikan content tidak kosong jika title ada
    if "title" in clean and "content" not in clean:
        clean["content"] = clean["title"]
    return clean

def is_new_signal(url):
    """Mengecek apakah URL signal sudah ada (Thread-safe & Character-safe)."""
    # Encode URL agar karakter seperti '&' atau '?' tidak merusak query API
    safe_url = quote(url)
    query = f"url=eq.{safe_url}&select=id&limit=1"
    
    try:
        result = db.fetch_records("signals", query)
        return len(result) == 0
    except Exception as e:
        print(f"⚠️ Check duplicate failed for {url[:30]}: {e}")
        # Jika error, asumsikan baru saja agar tidak kehilangan data, 
        # tapi amankan dengan try-except di insert_record
        return True

def save_signal(signal):
    """Validasi, de-duplikasi, dan simpan signal."""
    clean_data = sanitize_signal(signal)
    
    if "url" not in clean_data or "title" not in clean_data:
        return False

    if not is_new_signal(clean_data["url"]):
        # Gunakan logging yang lebih ringkas agar log GitHub tidak terlalu panjang
        return False

    clean_data["processed"] = False 
    
    # db.insert_record sudah menggunakan timeout dan error handling
    success = db.insert_record("signals", clean_data)
    if success:
        print(f"✅ Ingested: {clean_data['title'][:50]}...")
    return success

def load_data_sources():
    """Memuat scraper secara dinamis."""
    modules = []
    # Path yang lebih absolut berdasarkan ROOT_DIR
    source_dir = ROOT_DIR / "agents" / "data_sources"
    
    if not source_dir.exists():
        print(f"⚠️ Source directory not found: {source_dir}")
        return []

    # Pastikan file __init__.py ada di agents/data_sources/
    for file in source_dir.glob("*.py"):
        if file.name.startswith("__") or file.name == "base.py":
            continue
            
        module_name = f"agents.data_sources.{file.stem}"
        try:
            # Reload jika sudah pernah diimport untuk menghindari caching issue
            module = importlib.import_module(module_name)
            importlib.reload(module)
            
            if hasattr(module, "fetch"):
                modules.append(module)
            else:
                print(f"⚠️ Skipped {file.name}: No fetch() found.")
        except Exception as e:
            print(f"❌ Failed to load source {module_name}: {e}")
            
    return modules

def main():
    print("=== [AGENT] Global Trend Scanner ===")
    
    sources = load_data_sources()
    if not sources:
        print("❌ No active data sources found. Check agents/data_sources/ folder.")
        return

    print(f"📡 Active sources: {[s.__name__.split('.')[-1] for s in sources]}")

    total_new_signals = 0

    for source in sources:
        source_name = source.__name__.split('.')[-1]
        print(f"\n🔄 Source: {source_name.upper()}")
        
        try:
            # Berikan timeout internal jika scraper mendukung
            signals = source.fetch()
            
            if not signals:
                print(f"📭 No signals found.")
                continue

            count = 0
            for s in signals:
                if save_signal(s):
                    count += 1
            
            total_new_signals += count
            print(f"📊 Added {count} new items from {source_name}")
                    
        except Exception as e:
            print(f"❌ Crash in source {source_name}: {e}")

    print(f"\n=== Final: {total_new_signals} new signals added ===")

if __name__ == "__main__":
    main()
