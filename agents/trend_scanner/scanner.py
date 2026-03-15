import os
import sys
import importlib
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# -------------------------------------------------
# FIX PYTHONPATH (IMPORTANT FOR GITHUB ACTIONS)
# -------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


# -------------------------------------------------
# ENV
# -------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing SUPABASE environment variables")
    sys.exit(1)


# -------------------------------------------------
# HTTP SESSION WITH RETRY
# -------------------------------------------------

session = requests.Session()

retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

session.mount("https://", HTTPAdapter(max_retries=retries))


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# -------------------------------------------------
# VALID SIGNAL FIELDS (SCHEMA SAFE)
# -------------------------------------------------

VALID_FIELDS = {
    "source",
    "title",
    "url",
    "created_at"
}


# -------------------------------------------------
# CLEAN SIGNAL PAYLOAD
# -------------------------------------------------

def sanitize_signal(signal):

    clean = {}

    for k, v in signal.items():

        if k in VALID_FIELDS and v:

            clean[k] = v

    return clean


# -------------------------------------------------
# CHECK DUPLICATE URL
# -------------------------------------------------

def is_duplicate(url):

    try:

        r = session.get(
            f"{SUPABASE_URL}/rest/v1/signals",
            headers=headers,
            params={
                "select": "id",
                "url": f"eq.{url}",
                "limit": 1
            },
            timeout=10
        )

        if r.status_code != 200:
            return False

        data = r.json()

        return len(data) > 0

    except Exception as e:

        print("Duplicate check failed:", e)
        return False


# -------------------------------------------------
# SAVE SIGNAL
# -------------------------------------------------

def save_signal(signal):

    signal = sanitize_signal(signal)

    if "url" not in signal or "title" not in signal:
        return

    if is_duplicate(signal["url"]):
        print("Duplicate skipped:", signal["url"])
        return

    try:

        r = session.post(
            f"{SUPABASE_URL}/rest/v1/signals",
            headers=headers,
            json=signal,
            timeout=15
        )

        if r.status_code in [200, 201]:
            print("Inserted:", signal["title"][:60])

        else:
            print("Insert failed:", r.text)

    except Exception as e:

        print("Insert error:", e)


# -------------------------------------------------
# LOAD DATA SOURCES
# -------------------------------------------------

def load_sources():

    modules = []

    source_dir = ROOT_DIR / "agents" / "data_sources"

    for file in source_dir.glob("*.py"):

        if file.name == "__init__.py":
            continue

        module_name = file.stem

        try:

            module = importlib.import_module(
                f"agents.data_sources.{module_name}"
            )

            if hasattr(module, "fetch"):

                modules.append(module)

            else:

                print("Skipped (no fetch function):", module_name)

        except Exception as e:

            print("Failed loading source:", module_name)
            print(e)

    return modules


# -------------------------------------------------
# RUN SOURCES
# -------------------------------------------------

def run_sources():

    modules = load_sources()

    print("Sources detected:", len(modules))

    total = 0

    for m in modules:

        try:

            print("\nRunning source:", m.__name__)

            signals = m.fetch()

            if not signals:
                print("No signals returned")
                continue

            print("Signals fetched:", len(signals))

            for s in signals:

                save_signal(s)

                total += 1

        except Exception as e:

            print("Source failed:", m.__name__)
            print(e)

    print("\nTotal signals processed:", total)


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    print("================================")
    print("Running Trend Scanner")
    print("================================")

    run_sources()

    print("\nTrend scanning finished")


if __name__ == "__main__":
    main()
