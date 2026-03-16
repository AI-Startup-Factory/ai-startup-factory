import requests
from core.config import settings

class SupabaseClient:
    def __init__(self):
        self.headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"

    def fetch_records(self, table: str, query_params: str):
        url = f"{self.base_url}/{table}?{query_params}"
        r = requests.get(url, headers=self.headers)
        return r.json() if r.status_code == 200 else []

    def update_record(self, table: str, row_id: str, data: dict):
        url = f"{self.base_url}/{table}?id=eq.{row_id}"
        r = requests.patch(url, headers=self.headers, json=data)
        return r.status_code in [200, 204]

db = SupabaseClient()
