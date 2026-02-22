#!/usr/bin/env python3
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


def upload_image(file_path: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/assets",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": (Path(file_path).name, open(file_path, "rb"), "image/png")},
    )
    resp.raise_for_status()
    url = resp.json()["image_url"]
    print(f"  uploaded {Path(file_path).name} → {url}")
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


def main():
    if not API_KEY:
        sys.exit("KREA_API_KEY not set in .env")

    images_dir = os.getenv("TRAINING_IMAGES_DIR", "/training_images")
    style_name = os.getenv("STYLE_NAME", "my-style")

    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    image_files = sorted(f for ext in exts for f in Path(images_dir).glob(ext))

    if not image_files:
        sys.exit(f"No images found in {images_dir}")

    cache = json.loads(Path(URLS_CACHE).read_text()) if Path(URLS_CACHE).exists() else {}
    urls = []
    new_uploads = {}
    for f in image_files:
        name = Path(f).name
        if name in cache:
            print(f"  cached  {name} → {cache[name]}")
            urls.append(cache[name])
        else:
            url = upload_image(str(f))
            urls.append(url)
            new_uploads[name] = url
    if new_uploads:
        cache.update(new_uploads)
        Path(URLS_CACHE).write_text(json.dumps(cache, indent=2))

    payload = {
        "name": style_name,
        "urls": urls,
        "model": "qwen",
        "type": os.getenv("TRAIN_TYPE", "Style"),
    }
    if os.getenv("MAX_TRAIN_STEPS"):
        payload["max_train_steps"] = int(os.getenv("MAX_TRAIN_STEPS"))
    if os.getenv("TRIGGER_WORD"):
        payload["trigger_word"] = os.getenv("TRIGGER_WORD")

    print(f"\n── Training style '{style_name}' ──")
    print({k: f"[{len(v)} urls]" if k == "urls" else v for k, v in payload.items()})
    resp = requests.post(f"{BASE_URL}/styles/train", headers=auth(), json=payload)
    if not resp.ok:
        print(f"error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    job_id = resp.json()["job_id"]
    print(f"job started: {job_id}")

    print(f"\n── Polling (this can take several minutes) ──")
    result = poll_job(job_id)
    style_id = result["style_id"]

    print(f"\nDone!  STYLE_ID={style_id}")
    print(f"Add that to .env and run: make image")


if __name__ == "__main__":
    main()
