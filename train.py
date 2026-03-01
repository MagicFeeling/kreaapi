#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
from pathlib import Path

URLS_CACHE = "/app/uploaded_urls.json"

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KREA_API_KEY")
BASE_URL = "https://api.krea.ai"


def auth():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def upload_image(file_path: Path) -> str:
    resp = requests.post(
        f"{BASE_URL}/assets",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": (file_path.name, open(file_path, "rb"), "image/png")},
    )
    resp.raise_for_status()
    url = resp.json()["image_url"]
    print(f"  uploaded {file_path.name} → {url}")
    return url


def poll_job(job_id: str, interval: int = 15, timeout: int = 7200) -> dict:
    deadline = time.time() + timeout
    while True:
        resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=auth())
        resp.raise_for_status()
        data = resp.json()
        status = data["status"]
        print(f"  [{job_id}] {status}")
        if status == "completed":
            return data.get("result", {})
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}: {data}")
        if time.time() > deadline:
            raise TimeoutError(f"Job {job_id} timed out")
        time.sleep(interval)


def load_cache() -> dict:
    path = Path(URLS_CACHE)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    # migrate old format {name: url_string} → {name: {"url": ..., "sha256": ...}}
    migrated = {}
    for name, entry in raw.items():
        if isinstance(entry, str):
            migrated[name] = {"url": entry, "sha256": None}  # hash unknown → will re-upload
        else:
            migrated[name] = entry
    return migrated


def save_cache(cache: dict) -> None:
    Path(URLS_CACHE).write_text(json.dumps(cache, indent=2))


def main():
    if not API_KEY:
        sys.exit("KREA_API_KEY not set in .env")

    images_dir = os.getenv("TRAINING_IMAGES_DIR", "/training_images")
    style_name = os.getenv("STYLE_NAME", "my-style")

    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    image_files = sorted(f for ext in exts for f in Path(images_dir).glob(ext))

    if not image_files:
        sys.exit(f"No images found in {images_dir}")

    cache = load_cache()
    urls = []
    updated = False

    for f in image_files:
        name = f.name
        current_hash = sha256(f)
        entry = cache.get(name)

        if entry and entry.get("sha256") == current_hash:
            print(f"  cached  {name} → {entry['url']}")
            urls.append(entry["url"])
        else:
            if entry:
                print(f"  stale   {name} (content changed) — re-uploading")
            url = upload_image(f)
            cache[name] = {"url": url, "sha256": current_hash}
            urls.append(url)
            updated = True

    if updated:
        save_cache(cache)
        print(f"  waiting 5s for uploads to propagate...")
        time.sleep(5)

    payload = {
        "name": style_name,
        "urls": urls,
        "model": os.getenv("TRAIN_MODEL", "qwen2512"),
        "type": os.getenv("TRAIN_TYPE", "Style"),
    }
    if os.getenv("MAX_TRAIN_STEPS"):
        payload["max_train_steps"] = int(os.getenv("MAX_TRAIN_STEPS"))
    if os.getenv("TRIGGER_WORD"):
        payload["trigger_word"] = os.getenv("TRIGGER_WORD")

    print(f"\n── Training style '{style_name}' with {len(urls)} images ──")
    job_id = None
    for attempt in range(1, 4):
        resp = requests.post(f"{BASE_URL}/styles/train", headers=auth(), json=payload)
        if resp.ok:
            job_id = resp.json()["job_id"]
            break
        print(f"error {resp.status_code} (attempt {attempt}/3): {resp.text}")
        if resp.status_code != 500 or attempt == 3:
            resp.raise_for_status()
        print(f"retrying in 10s...")
        time.sleep(10)

    print(f"job started: {job_id}")


    print(f"\n── Polling (this can take several minutes) ──")
    result = poll_job(job_id)
    style_id = result["style_id"]

    print(f"\nDone!  STYLE_ID={style_id}")
    print(f"Add that to .env and run: make image")


if __name__ == "__main__":
    main()
