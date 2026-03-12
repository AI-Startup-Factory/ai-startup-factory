import os
import importlib
import requests
from pathlib import Path


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def save_signal(signal):

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/signals",
        headers=headers,
        json=signal
    )

    if r.status_code not in [200, 201]:
        print("Insert failed:", r.text)


def load_sources():

    modules = []

    source_dir = Path(__file__).resolve().parents[1] / "data_sources"

    for file in source_dir.glob("*.py"):

        if file.name == "__init__.py":
            continue

        module_name = file.stem

        module = importlib.import_module(
            f"agents.data_sources.{module_name}"
        )

        modules.append(module)

    return modules


def run_sources():

    modules = load_sources()

    print("Sources detected:", len(modules))

    for m in modules:

        try:

            signals = m.fetch()

            print(m.__name__, "signals:", len(signals))

            for s in signals:
                save_signal(s)

        except Exception as e:

            print("Source failed:", m.__name__)
            print(e)


def main():

    print("Running Trend Scanner")

    run_sources()

    print("Trend scanning finished")


if __name__ == "__main__":
    main()
