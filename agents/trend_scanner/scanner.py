import os
import importlib
import requests
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing Supabase environment variables")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# -----------------------------------
# SAVE SIGNAL
# -----------------------------------
def save_signal(signal):

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/signals",
        headers=headers,
        json=signal
    )

    if r.status_code not in [200, 201]:
        print("Insert failed:", r.text)


# -----------------------------------
# LOAD SOURCE MODULES
# -----------------------------------
def load_sources():

    source_dir = Path("agents/data_sources")

    modules = []

    for file in source_dir.glob("*.py"):

        name = file.stem

        module = importlib.import_module(
            f"agents.data_sources.{name}"
        )

        modules.append(module)

    return modules


# -----------------------------------
# RUN SCANNERS
# -----------------------------------
def run_sources():

    modules = load_sources()

    print(f"Loaded {len(modules)} data sources\n")

    for m in modules:

        try:

            print(f"Running source: {m.__name__}")

            signals = m.fetch()

            for s in signals:
                save_signal(s)

            print(f"Collected {len(signals)} signals\n")

        except Exception as e:

            print("Source failed:", m.__name__)
            print(e)


# -----------------------------------
# MAIN
# -----------------------------------
def main():

    print("Starting Trend Scanner\n")

    run_sources()

    print("Trend scanning complete")


if __name__ == "__main__":
    main()
