"""
Builds all_wallpaper_api.json for the Depth Lock Screen app from the category folders.

Add new wallpapers: drop images into a category folder (or a new folder = new tab), then run
    python update_json.py
- Existing wallpapers keep their id (favourites / applied wallpaper stay correct).
- New images get the next ids, a small preview in preview/, and appear in their category tab.
- base_url and tab names already in all_wallpaper_api.json are kept.
Then push the folder to GitHub.
"""
import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "all_wallpaper_api.json")
PREVIEW_DIR = "preview"
PREVIEW_W = 360
DEFAULT_BASE_URL = "https://cdn.jsdelivr.net/gh/USERNAME/REPO@main/"

# Tab order (folders not listed here come after, alphabetically) and default tab names
ORDER = ["superhero", "anime", "animal", "vehicle", "cartoon", "nature", "people", "architecture",
         "abstract", "space", "mix", "games", "sports", "pixel"]
NAMES = {"superhero": "Superheroes", "anime": "Anime", "animal": "Animals", "vehicle": "Cars & Bikes",
         "cartoon": "Cartoons", "nature": "Nature", "people": "People", "architecture": "Architecture",
         "abstract": "Abstract", "space": "Space", "mix": "Mix", "games": "Games", "sports": "Sports",
         "pixel": "Pixel Art"}
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


def number(name):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 0


old = {}
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as fh:
        old = json.load(fh)
base_url = old.get("base_url", DEFAULT_BASE_URL)
names = {c["key"]: c["name"] for c in old.get("categories", []) if "key" in c and "name" in c}
ids = {d["og_file"]: d["id"] for d in old.get("data", [])}
next_id = max(ids.values(), default=0) + 1

folders = [d for d in os.listdir(ROOT)
           if os.path.isdir(os.path.join(ROOT, d)) and d != PREVIEW_DIR and not d.startswith(".")]
cats = [c for c in ORDER if c in folders] + sorted(c for c in folders if c not in ORDER)

data, categories, added = [], [], 0
for cat in cats:
    files = sorted((f for f in os.listdir(os.path.join(ROOT, cat)) if f.lower().endswith(IMAGE_EXT)), key=number)
    if not files:
        continue
    categories.append({"key": cat, "name": names.get(cat, NAMES.get(cat, cat.replace("_", " ").title()))})
    os.makedirs(os.path.join(ROOT, PREVIEW_DIR, cat), exist_ok=True)
    for f in files:
        og = "%s/%s" % (cat, f)
        stem = os.path.splitext(f)[0]
        preview = "%s/%s/%s.jpg" % (PREVIEW_DIR, cat, stem)
        preview_abs = os.path.join(ROOT, PREVIEW_DIR, cat, stem + ".jpg")
        if not os.path.exists(preview_abs):
            im = Image.open(os.path.join(ROOT, cat, f)).convert("RGB")
            im.resize((PREVIEW_W, round(im.height * PREVIEW_W / im.width)), Image.LANCZOS) \
                .save(preview_abs, "JPEG", quality=82, optimize=True, progressive=True)
        if og not in ids:
            ids[og] = next_id
            next_id += 1
            added += 1
        data.append({"id": ids[og], "category": cat, "og_file": og, "preview_file": preview})

api = {"status": "success", "base_url": base_url, "categories": categories, "data": data}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(api, fh, indent=2, ensure_ascii=False)
print("wallpapers: %d (new: %d), categories: %d" % (len(data), added, len(categories)))
