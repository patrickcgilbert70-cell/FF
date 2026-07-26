#!/usr/bin/env python3
"""
Analyzes a folder of game camera photos and produces a daily activity summary.

For each photo, Claude vision is used to read the camera's burned-in date/time
stamp and count animals present (pigs, turkeys, doe, bucks, cows). Results are
cached on disk so re-running only analyzes new photos.
"""

import sys
import os
import re
import json
import base64
import argparse
import hashlib
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from PIL import Image, ExifTags
except ImportError:
    print("Error: Pillow module not found.")
    print("Please install it using: pip install Pillow")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("Error: anthropic module not found.")
    print("Please install it using: pip install anthropic")
    sys.exit(1)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SPECIES_FIELDS = ["pigs", "turkeys", "does", "bucks", "cows"]
SPECIES_LABELS = {
    "pigs": "Pigs",
    "turkeys": "Turkeys",
    "does": "Female Doe",
    "bucks": "Male Bucks",
    "cows": "Cows",
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_IMAGE_DIMENSION = 1280

CLASSIFY_PROMPT = """You are analyzing a single photo taken by an outdoor game/trail camera.

1. Read the date/time stamp that the camera has overlaid on the photo (usually in a
   corner). Convert it to 24-hour ISO format "YYYY-MM-DD HH:MM:SS". If no stamp is
   visible or it is unreadable, set capture_time to null.
2. Count the animals visible in the photo for each of these categories:
   - pigs (wild hogs/boars)
   - turkeys
   - does (female deer, no antlers)
   - bucks (male deer, with antlers)
   - cows (cattle)

Respond with ONLY valid JSON (no markdown fences, no extra text) in exactly this form:
{"capture_time": "YYYY-MM-DD HH:MM:SS" or null, "pigs": 0, "turkeys": 0, "does": 0, "bucks": 0, "cows": 0}
"""


def find_photos(input_dir):
    photos = []
    for name in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            photos.append(os.path.join(input_dir, name))
    return photos


def file_cache_key(path):
    stat = os.stat(path)
    return f"{os.path.basename(path)}:{stat.st_size}:{int(stat.st_mtime)}"


def load_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache_path, cache):
    tmp_path = cache_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp_path, cache_path)


def get_exif_datetime(image):
    try:
        exif = image.getexif()
        if not exif:
            return None
        tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        raw = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
        if raw:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None


def prepare_image_payload(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        exif_dt = get_exif_datetime(img)
        w, h = img.size
        scale = min(1.0, MAX_IMAGE_DIMENSION / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
    return b64, exif_dt


def parse_model_json(text):
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in response: {text!r}")
    return json.loads(match.group(0))


def classify_photo(client, model, path):
    b64, exif_dt = prepare_image_payload(path)

    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": CLASSIFY_PROMPT},
                ],
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    data = parse_model_json(text)

    capture_time = data.get("capture_time")
    approximate = False
    if not capture_time:
        if exif_dt:
            capture_time = exif_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            capture_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        approximate = True

    result = {
        "filename": os.path.basename(path),
        "capture_time": capture_time,
        "approximate_time": approximate,
    }
    for field in SPECIES_FIELDS:
        result[field] = int(data.get(field, 0) or 0)
    return result


def analyze_folder(input_dir, cache_path, model, max_workers, api_key):
    photos = find_photos(input_dir)
    if not photos:
        print(f"No photos found in {input_dir}")
        return []

    cache = load_cache(cache_path)
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    to_process = []
    for path in photos:
        key = file_cache_key(path)
        if key not in cache:
            to_process.append((key, path))

    print(f"Found {len(photos)} photos, {len(to_process)} need analysis "
          f"({len(photos) - len(to_process)} already cached).")

    if to_process:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(classify_photo, client, model, path): (key, path)
                for key, path in to_process
            }
            done = 0
            for future in as_completed(futures):
                key, path = futures[future]
                done += 1
                try:
                    cache[key] = future.result()
                except Exception as exc:
                    print(f"  [{done}/{len(to_process)}] FAILED {os.path.basename(path)}: {exc}")
                    continue
                print(f"  [{done}/{len(to_process)}] analyzed {os.path.basename(path)}")
                if done % 20 == 0:
                    save_cache(cache_path, cache)
        save_cache(cache_path, cache)

    records = [cache[file_cache_key(path)] for path in photos if file_cache_key(path) in cache]
    return records


def build_report(records):
    for r in records:
        r["_dt"] = datetime.strptime(r["capture_time"], "%Y-%m-%d %H:%M:%S")
        r["_date"] = r["_dt"].date()

    lines = []
    total = len(records)
    overall = {field: sum(r[field] for r in records) for field in SPECIES_FIELDS}

    lines.append("# Game Camera Summary\n")
    lines.append("## Overall Summary (All Days)\n")
    lines.append(f"- **Total Pictures**: {total}")
    for field in SPECIES_FIELDS:
        lines.append(f"- **{SPECIES_LABELS[field]}**: {overall[field]}")
    lines.append("")

    lines.append("## Daily Breakdown\n")
    days = sorted(set(r["_date"] for r in records))
    for day in days:
        day_records = [r for r in records if r["_date"] == day]
        lines.append(f"### {day.strftime('%A, %B %d, %Y')}\n")
        lines.append(f"- **Total Pictures**: {len(day_records)}")
        for field in SPECIES_FIELDS:
            lines.append(f"- **{SPECIES_LABELS[field]}**: {sum(r[field] for r in day_records)}")

        pig_records = sorted((r for r in day_records if r["pigs"] > 0), key=lambda r: r["_dt"])
        if pig_records:
            first_pig = pig_records[0]
            lines.append(f"- **First Pig Sighting**: {first_pig['_dt'].strftime('%I:%M %p')} "
                          f"({first_pig['filename']})")
        else:
            lines.append("- **First Pig Sighting**: none")

        six_pm = datetime.combine(day, datetime.min.time()) + timedelta(hours=18)
        evening_pig_records = [r for r in pig_records if r["_dt"] >= six_pm]
        if evening_pig_records:
            first_evening_pig = evening_pig_records[0]
            lines.append(f"- **First Pig Sighting After 6:00 PM**: "
                          f"{first_evening_pig['_dt'].strftime('%I:%M %p')} "
                          f"({first_evening_pig['filename']})")
        else:
            lines.append("- **First Pig Sighting After 6:00 PM**: none")

        if pig_records:
            top_pig_photo = max(day_records, key=lambda r: r["pigs"])
            lines.append(f"- **Photo With Most Pigs**: {top_pig_photo['filename']} "
                          f"({top_pig_photo['pigs']} pigs)")
        else:
            lines.append("- **Photo With Most Pigs**: none")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize game camera photos by day.")
    parser.add_argument("--input", required=True, help="Folder containing photos to analyze")
    parser.add_argument("--cache", default=None,
                         help="Path to cache JSON file (default: <input>/analysis_cache.json)")
    parser.add_argument("--output", default="game_camera_summary.md",
                         help="Path to write the markdown report")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model to use for vision analysis")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent API requests")
    parser.add_argument("--api-key", default=None,
                         help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    if not os.path.isdir(input_dir):
        print(f"Error: input folder not found: {input_dir}")
        sys.exit(1)

    cache_path = args.cache or os.path.join(input_dir, "analysis_cache.json")

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: no Anthropic API key found. Set ANTHROPIC_API_KEY or pass --api-key.")
        sys.exit(1)

    records = analyze_folder(input_dir, cache_path, args.model, args.workers, api_key)
    if not records:
        sys.exit(0)

    report = build_report(records)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
