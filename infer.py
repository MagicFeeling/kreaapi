#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KREA_API_KEY")
BASE_URL = "https://api.krea.ai"


def auth():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def poll_job(job_id: str, interval: int = 5, timeout: int = 300) -> dict:
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
            urls = data.get("result", {}).get("urls", [])
            if any("nsfw_replacement" in u for u in urls):
                sys.exit("Blocked: prompt was flagged as NSFW. Change your PROMPT in .env and try again.")
            raise RuntimeError(f"Job {job_id} {status}: {data}")
        if time.time() > deadline:
            raise TimeoutError(f"Job {job_id} timed out")
        time.sleep(interval)


def main():
    if not API_KEY:
        sys.exit("KREA_API_KEY not set in .env")

    style_id = os.getenv("STYLE_ID")
    if not style_id:
        sys.exit("STYLE_ID not set in .env — run make train first")

    prompt = os.getenv("PROMPT", "a beautiful portrait")
    strength = float(os.getenv("STYLE_STRENGTH", "0.8"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = os.getenv("OUTPUT_PATH", f"/output/{style_id}_{timestamp}_s{strength:.2f}.png")

    aspect = os.getenv("ASPECT_RATIO", "1:1")
    w_ratio, h_ratio = map(int, aspect.split(":"))
    base = 1024
    width = base if w_ratio >= h_ratio else int(base * w_ratio / h_ratio)
    height = base if h_ratio >= w_ratio else int(base * h_ratio / w_ratio)
    # round to nearest 8
    width = round(width / 8) * 8
    height = round(height / 8) * 8

    payload = {
        "prompt": prompt,
        "negative_prompt": os.getenv("NEGATIVE_PROMPT", ""),
        "width": width,
        "height": height,
        "num_inference_steps": int(os.getenv("STEPS", 30)),
        "cfg_scale": float(os.getenv("CFG_SCALE", 4)),
        "styles": [{"id": style_id, "strength": strength}],
    }

    print(f"Prompt  : {prompt}")
    print(f"Style   : {style_id} (strength {strength})")

    resp = requests.post(
        f"{BASE_URL}/generate/image/qwen/2512",
        headers=auth(),
        json=payload,
    )
    resp.raise_for_status()
    job_id = resp.json()["job_id"]
    print(f"job started: {job_id}")

    result = poll_job(job_id)

    urls = result.get("urls") or []
    if not urls:
        sys.exit(f"No image URL in result: {result}")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    img = requests.get(urls[0], stream=True)
    img.raise_for_status()
    with open(output, "wb") as f:
        for chunk in img.iter_content(8192):
            f.write(chunk)

    print(f"saved → {output}")


if __name__ == "__main__":
    main()
