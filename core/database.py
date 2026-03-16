# core/database.py
import requests
from core.config import settings

class SupabaseClient:
    def __init__(self):
        self.headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"

    def fetch_records(self, table: str, query_params: str):
        url = f"{self.base_url}/{table}?{query_params}"
        try:
            # TAMBAHKAN timeout=10
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"❌ Database Timeout/Error: {e}")
            return []
