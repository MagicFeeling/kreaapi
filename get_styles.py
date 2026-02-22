#!/usr/bin/env python3
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KREA_API_KEY")
BASE_URL = "https://api.krea.ai"


def main():
    if not API_KEY:
        sys.exit("KREA_API_KEY not set in .env")

    for f in ("user", "shared"):
        resp = requests.get(
            f"{BASE_URL}/styles",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"filter": f, "limit": 100},
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        print(f"\n── {f} ({len(items)}) ──")
        for s in items:
            print(f"  {s.get('id',''):<15} {s.get('name','')}")


if __name__ == "__main__":
    main()
