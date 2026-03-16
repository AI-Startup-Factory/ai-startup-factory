import requests
from core.config import settings

class SupabaseClient:
    def __init__(self):
        self.headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal" # Mengoptimalkan performa karena kita tidak butuh data balikan setelah insert
        }
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"

    def fetch_records(self, table: str, query_params: str):
        url = f"{self.base_url}/{table}?{query_params}"
        r = requests.get(url, headers=self.headers)
        return r.json() if r.status_code == 200 else []

    def insert_record(self, table: str, data: dict):
        """Metode untuk memasukkan data baru ke tabel (Digunakan oleh Ingestion)."""
        url = f"{self.base_url}/{table}"
        r = requests.post(url, headers=self.headers, json=data)
        # 201 Created adalah status sukses untuk POST di PostgREST (Supabase)
        return r.status_code in [200, 201, 204]

    def update_record(self, table: str, row_id: str, data: dict):
        url = f"{self.base_url}/{table}?id=eq.{row_id}"
        r = requests.patch(url, headers=self.headers, json=data)
        return r.status_code in [200, 204]

db = SupabaseClient()
