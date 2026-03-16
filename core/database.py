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
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"❌ Database Fetch Error: {e}")
            return []

    def insert_record(self, table: str, data: dict):
        url = f"{self.base_url}/{table}"
        try:
            r = requests.post(url, headers=self.headers, json=data, timeout=10)
            return r.status_code in [200, 201, 204]
        except Exception as e:
            print(f"❌ Database Insert Error: {e}")
            return False

    def update_record(self, table: str, row_id: str, data: dict):
        url = f"{self.base_url}/{table}?id=eq.{row_id}"
        try:
            r = requests.patch(url, headers=self.headers, json=data, timeout=10)
            return r.status_code in [200, 204]
        except Exception as e:
            print(f"❌ Database Update Error: {e}")
            return False

# BARIS CRUCIAL YANG HILANG:
db = SupabaseClient()
