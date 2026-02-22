#!/usr/bin/env python3
"""Binary search to find which uploaded image Krea flags as unsafe."""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KREA_API_KEY")
BASE_URL = "https://api.krea.ai"


def auth():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def is_safe(urls: list[str]) -> bool:
    resp = requests.post(
        f"{BASE_URL}/styles/train",
        headers=auth(),
        json={"name": "_safety_check", "urls": urls, "model": "qwen", "type": "Style"},
    )
    if resp.status_code == 400 and "Unsafe" in resp.text:
        return False
    # any other response (including 500) means the batch passed safety
    return True


def find_unsafe(urls: list[str], names: list[str]) -> list[str]:
    if len(urls) == 1:
        print(f"  FOUND unsafe image: {names[0]}")
        return names
    mid = len(urls) // 2
    left_urls, left_names = urls[:mid], names[:mid]
    right_urls, right_names = urls[mid:], names[mid:]
    print(f"  checking {len(left_urls)} images: {left_names[0]} … {left_names[-1]}")
    bad = []
    if not is_safe(left_urls):
        bad += find_unsafe(left_urls, left_names)
    print(f"  checking {len(right_urls)} images: {right_names[0]} … {right_names[-1]}")
    if not is_safe(right_urls):
        bad += find_unsafe(right_urls, right_names)
    return bad


def main():
    cache_path = Path("uploaded_urls.json")
    if not cache_path.exists():
        sys.exit("uploaded_urls.json not found")

    cache = json.loads(cache_path.read_text())
    names = sorted(cache.keys())
    urls = [cache[n] for n in names]

    print(f"Binary searching {len(urls)} images for unsafe content...\n")
    bad = find_unsafe(urls, names)

    if bad:
        print(f"\nRemove these from uploaded_urls.json and training_images/:")
        for n in bad:
            print(f"  {n}")
    else:
        print("\nNo unsafe images found (safety check may have passed this time).")


if __name__ == "__main__":
    main()
