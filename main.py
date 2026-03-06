#!/usr/bin/env python3
"""Swipestack car decks — reads Excel, fetches data + images, generates PWAs."""

import hashlib
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote_plus, urlencode

# ---------------------------------------------------------------------------
# Ensure dependencies
# ---------------------------------------------------------------------------
def ensure_deps():
    for pkg, imp in [("openpyxl", "openpyxl"), ("requests", "requests"), ("Pillow", "PIL")]:
        try:
            __import__(imp)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure_deps()

import openpyxl
import requests
from PIL import Image
from io import BytesIO

from car_data import CAR_DATA, MODEL_MAP
from swipestack import swipestack

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
CACHE_FILE = OUTPUT_DIR / "cache.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

# ---------------------------------------------------------------------------
# Excel reader
# ---------------------------------------------------------------------------
def read_sheet(wb, sheet_name):
    """Return list of dicts with keys: model, years, comma_note."""
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    cars = []
    for row in rows[1:]:
        model_raw = row[0]
        years_str = str(row[1]) if row[1] else ""
        comma_note = row[2]
        # Strip parenthetical qualifiers for dedup
        model_clean = re.sub(r"\s*\(.*?\)\s*", " ", model_raw).strip()
        model_clean = re.sub(r"\s+", " ", model_clean)
        years = [y.strip() for y in years_str.split(",") if y.strip()]
        cars.append({
            "model_raw": model_raw,
            "model": model_clean,
            "years": years,
            "comma_note": comma_note,
        })
    return cars

def consolidate_cars(cars):
    """Merge rows that differ only by year range into single entries."""
    merged = {}
    for c in cars:
        key = c["model"]
        if key in merged:
            # Merge years (unique, sorted)
            existing_years = set(merged[key]["years"])
            existing_years.update(c["years"])
            merged[key]["years"] = sorted(existing_years)
            # Keep first non-None comma_note
            if not merged[key]["comma_note"] and c["comma_note"]:
                merged[key]["comma_note"] = c["comma_note"]
        else:
            merged[key] = {
                "model": c["model"],
                "years": list(c["years"]),
                "comma_note": c["comma_note"],
            }
    return list(merged.values())

# ---------------------------------------------------------------------------
# fueleconomy.gov API
# ---------------------------------------------------------------------------
FUEL_API = "https://www.fueleconomy.gov/ws/rest/vehicle"
FUEL_HEADERS = {"Accept": "application/xml"}

def fetch_fuel_data(make, model_name, year, cache):
    """Fetch MPG + fuel data from fueleconomy.gov. Returns dict or None."""
    cache_key = f"fuel:{make}:{model_name}:{year}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        session = requests.Session()
        session.headers.update(FUEL_HEADERS)

        # options endpoint returns vehicle IDs as menuItem/value
        url = f"{FUEL_API}/menu/options?year={year}&make={make}&model={quote_plus(model_name)}"
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.text)
        items = root.findall(".//menuItem")
        if not items:
            return None

        vehicle_id = items[0].find("value").text
        r_veh = session.get(f"{FUEL_API}/{vehicle_id}", timeout=10)
        if r_veh.status_code != 200:
            return None

        vroot = ET.fromstring(r_veh.text)
        result = {
            "city_mpg": _xml_text(vroot, "city08"),
            "highway_mpg": _xml_text(vroot, "highway08"),
            "combined_mpg": _xml_text(vroot, "comb08"),
            "fuel_type": _xml_text(vroot, "fuelType1"),
            "drive": _xml_text(vroot, "drive"),
            "cylinders": _xml_text(vroot, "cylinders"),
            "displacement": _xml_text(vroot, "displ"),
            "transmission": _xml_text(vroot, "trany"),
            "vehicle_class": _xml_text(vroot, "VClass"),
        }
        cache[cache_key] = result
        return result

    except Exception as e:
        print(f"  [!] Fuel API error for {make} {model_name} {year}: {e}")
        return None


def _xml_text(root, tag):
    el = root.find(tag)
    return el.text if el is not None else None

# ---------------------------------------------------------------------------
# DuckDuckGo image search
# ---------------------------------------------------------------------------
DDG_URL = "https://duckduckgo.com/"
DDG_IMG_URL = "https://duckduckgo.com/i.js"

def fetch_images(slug, query, count=4, cache=None):
    """Download images via DuckDuckGo. Returns list of relative paths."""
    if cache is None:
        cache = {}
    cache_key = f"images:{slug}"
    img_dir = IMAGES_DIR / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    # Check if we already have enough images on disk
    existing = sorted(img_dir.glob("*.jpg"))
    if len(existing) >= count:
        return [str(p.relative_to(OUTPUT_DIR)) for p in existing[:count]]

    if cache_key in cache:
        paths = cache[cache_key]
        if all(os.path.exists(OUTPUT_DIR / p) for p in paths) and len(paths) >= count:
            return paths

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://duckduckgo.com/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })

    try:
        # Get vqd token
        r = session.post("https://duckduckgo.com", data={"q": query}, timeout=10)
        vqd_match = re.search(r'vqd=([^&"\s;]+)', r.text)
        if not vqd_match:
            print(f"  [!] No vqd token for {slug}")
            return _fallback_images(slug, count)

        vqd = vqd_match.group(1)
        session.headers["x-vqd-4"] = vqd

        # Fetch image results
        r2 = session.get(DDG_IMG_URL, params={
            "l": "us-en", "o": "json", "q": query, "vqd": vqd, "f": ",,,,,", "p": "1",
        }, timeout=10)
        if r2.status_code != 200:
            print(f"  [!] DDG image search failed for {slug}: {r2.status_code}")
            return _fallback_images(slug, count)

        results = r2.json().get("results", [])
        if not results:
            print(f"  [!] No image results for {slug}")
            return _fallback_images(slug, count)

        # Download top images
        saved = []
        dl_session = requests.Session()
        dl_session.headers["User-Agent"] = session.headers["User-Agent"]
        for result in results:
            if len(saved) >= count:
                break
            img_url = result.get("image")
            if not img_url:
                continue
            try:
                img_r = dl_session.get(img_url, timeout=8)
                if img_r.status_code != 200 or len(img_r.content) < 10240:
                    continue
                img = Image.open(BytesIO(img_r.content))
                img = img.convert("RGB")
                if img.width > 800:
                    ratio = 800 / img.width
                    img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
                fname = f"{len(saved) + 1}.jpg"
                fpath = img_dir / fname
                img.save(fpath, "JPEG", quality=82)
                saved.append(str(fpath.relative_to(OUTPUT_DIR)))
            except Exception:
                continue

        if saved:
            cache[cache_key] = saved
            return saved

    except Exception as e:
        print(f"  [!] Image fetch error for {slug}: {e}")

    return _fallback_images(slug, count)


def _fallback_images(slug, count):
    """Return any existing images or empty list."""
    img_dir = IMAGES_DIR / slug
    existing = sorted(img_dir.glob("*.jpg"))
    return [str(p.relative_to(OUTPUT_DIR)) for p in existing[:count]]


def fetch_images_by_angle(slug, queries, cache=None):
    """Fetch one image per query (each query = a different angle). Returns list of relative paths."""
    if cache is None:
        cache = {}
    cache_key = f"images_v2:{slug}"
    img_dir = IMAGES_DIR / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    # Check cache
    if cache_key in cache:
        paths = cache[cache_key]
        if all(os.path.exists(OUTPUT_DIR / p) for p in paths) and len(paths) >= len(queries):
            return paths

    # Check existing files with angle naming
    angle_names = ["front", "rear", "interior", "side"]
    existing = []
    for name in angle_names:
        fpath = img_dir / f"{name}.jpg"
        if fpath.exists():
            existing.append(str(fpath.relative_to(OUTPUT_DIR)))
    if len(existing) >= len(queries):
        return existing

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://duckduckgo.com/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })

    saved = []
    dl_session = requests.Session()
    dl_session.headers["User-Agent"] = session.headers["User-Agent"]

    for idx, query in enumerate(queries):
        fname = angle_names[idx] if idx < len(angle_names) else f"img{idx+1}"
        fpath = img_dir / f"{fname}.jpg"
        if fpath.exists():
            saved.append(str(fpath.relative_to(OUTPUT_DIR)))
            continue

        try:
            # Get vqd token
            r = session.post("https://duckduckgo.com", data={"q": query}, timeout=10)
            vqd_match = re.search(r'vqd=([^&"\s;]+)', r.text)
            if not vqd_match:
                continue

            vqd = vqd_match.group(1)
            s2 = requests.Session()
            s2.headers.update(session.headers)
            s2.headers["x-vqd-4"] = vqd

            r2 = s2.get(DDG_IMG_URL, params={
                "l": "us-en", "o": "json", "q": query, "vqd": vqd, "f": ",,,,,", "p": "1",
            }, timeout=10)
            if r2.status_code != 200:
                continue

            results = r2.json().get("results", [])
            # Try each result until one works
            for result in results[:8]:
                img_url = result.get("image")
                if not img_url:
                    continue
                try:
                    img_r = dl_session.get(img_url, timeout=8)
                    if img_r.status_code != 200 or len(img_r.content) < 10240:
                        continue
                    img = Image.open(BytesIO(img_r.content))
                    img = img.convert("RGB")
                    if img.width > 800:
                        ratio = 800 / img.width
                        img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
                    img.save(fpath, "JPEG", quality=82)
                    saved.append(str(fpath.relative_to(OUTPUT_DIR)))
                    break
                except Exception:
                    continue
        except Exception:
            continue

    if saved:
        cache[cache_key] = saved
    return saved if saved else _fallback_images(slug, len(queries))

# ---------------------------------------------------------------------------
# Diesel detection & gas-equivalent MPG
# ---------------------------------------------------------------------------
DIESEL_KEYWORDS = ["GTD", "Diesel", "TDI", "CDI", "dCi"]
DIESEL_PRICE_PER_GAL = 3.85
GAS_PRICE_PER_GAL = 3.45

def is_diesel(model_name, fuel_data):
    """Check if a car is diesel based on name or API fuel type."""
    if any(kw.lower() in model_name.lower() for kw in DIESEL_KEYWORDS):
        return True
    if fuel_data and fuel_data.get("fuel_type"):
        ft = fuel_data["fuel_type"].lower()
        if "diesel" in ft:
            return True
    return False

def gas_equiv_mpg(diesel_mpg):
    """Diesel MPG * 0.84 for energy-equivalent comparison."""
    try:
        return round(float(diesel_mpg) * 0.84, 1)
    except (ValueError, TypeError):
        return None

# ---------------------------------------------------------------------------
# Build item dict for swipestack
# ---------------------------------------------------------------------------
def make_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def build_item(car, deck_type, fuel_data, image_paths):
    """Build a swipestack item dict from car data."""
    model = car["model"]
    data = CAR_DATA.get(model, {})
    years = car["years"]
    year_range = f"{min(years)}-{max(years)}" if len(years) > 1 else years[0]
    slug = make_slug(model)
    mapping = MODEL_MAP.get(model)
    region = "eu" if mapping and mapping[1] is None else "us"

    # Determine if diesel
    diesel = is_diesel(model, fuel_data)

    # Build stats
    stats = []

    # MPG from API or fallback
    if fuel_data and fuel_data.get("city_mpg"):
        city = fuel_data["city_mpg"]
        hwy = fuel_data["highway_mpg"]
        if diesel:
            stats.append({"icon": "fuel", "label": "Actual MPG", "value": f"{city}/{hwy}", "note": "city/hwy"})
            ge_city = gas_equiv_mpg(city)
            ge_hwy = gas_equiv_mpg(hwy)
            if ge_city and ge_hwy:
                stats.append({"icon": "info", "label": "Gas-Equiv MPG", "value": f"{ge_city}/{ge_hwy}", "note": "energy-adjusted"})
                cost_diesel = DIESEL_PRICE_PER_GAL / float(fuel_data.get("combined_mpg", city))
                cost_gas_avg = GAS_PRICE_PER_GAL / 28  # avg gas car
                stats.append({"icon": "dollar", "label": "Cost/mile", "value": f"~${cost_diesel:.3f}", "note": f"diesel vs ~${cost_gas_avg:.3f} gas avg"})
        else:
            stats.append({"icon": "fuel", "label": "MPG", "value": f"{city}/{hwy}", "note": "city/hwy"})

    # 0-60
    if data.get("zero_to_sixty"):
        stats.append({"icon": "gauge", "label": "0-60", "value": data["zero_to_sixty"], "note": None})

    # Engine
    if data.get("engine"):
        stats.append({"icon": "engine", "label": "Engine", "value": data["engine"], "note": None})

    # Power (hot hatches)
    if data.get("power_hp"):
        stats.append({"icon": "power", "label": "Power", "value": data["power_hp"], "note": None})

    # Drivetrain
    if data.get("driven_wheels"):
        stats.append({"icon": "drive", "label": "Drive", "value": data["driven_wheels"], "note": None})

    # Off-roader specific
    if data.get("ground_clearance"):
        stats.append({"icon": "clearance", "label": "Clearance", "value": data["ground_clearance"], "note": None})

    if data.get("tow_capacity"):
        stats.append({"icon": "tow", "label": "Towing", "value": data["tow_capacity"], "note": None})

    if data.get("four_wd_type"):
        stats.append({"icon": "compass", "label": "4WD Type", "value": data["four_wd_type"], "note": None})

    # Price
    if data.get("est_price_range"):
        stats.append({"icon": "dollar", "label": "Price Range", "value": data["est_price_range"], "note": "used market"})

    # Reliability
    if data.get("reliability"):
        stats.append({"icon": "wrench", "label": "Reliability", "value": data["reliability"], "note": None})

    # Fun factor
    if data.get("fun_factor"):
        stats.append({"icon": "bolt", "label": "Fun Factor", "value": data["fun_factor"], "note": None})

    # Parse min_price from est_price_range for budget filter
    min_price = 0
    price_str = data.get("est_price_range", "")
    price_match = re.search(r'[\$€](\d+)k', price_str)
    if price_match:
        min_price = int(price_match.group(1)) * 1000

    return {
        "id": slug,
        "name": model,
        "subtitle": year_range,
        "images": image_paths,
        "badge": "DIESEL" if diesel else None,
        "stats": stats,
        "pros": data.get("pros", []),
        "cons": data.get("cons", []),
        "vibe": data.get("description", ""),
        "footnote": car.get("comma_note"),
        "region": region,
        "min_price": min_price,
    }

# ---------------------------------------------------------------------------
# Process a single car (API + images)
# ---------------------------------------------------------------------------
def process_car(car, deck_type, cache):
    """Fetch fuel data + images for a single car. Returns item dict."""
    model = car["model"]
    years = car["years"]
    slug = make_slug(model)
    mapping = MODEL_MAP.get(model)

    print(f"  Processing {model}...")

    # Fuel data
    fuel_data = None
    if mapping and mapping[1] is not None:
        make, api_model = mapping
        # Use most recent year
        year = max(years)
        fuel_data = fetch_fuel_data(make, api_model, year, cache)
        if not fuel_data and len(years) > 1:
            # Try earlier years
            for y in sorted(years, reverse=True)[1:]:
                fuel_data = fetch_fuel_data(make, api_model, y, cache)
                if fuel_data:
                    break

    # Images — 4 distinct angles, one image per query
    search_year = max(years) if years else ""
    angle_queries = [
        f"{search_year} {model} front three quarter angle",
        f"{search_year} {model} rear three quarter angle",
        f"{search_year} {model} interior dashboard cockpit",
        f"{search_year} {model} side profile",
    ]
    image_paths = fetch_images_by_angle(slug, angle_queries, cache=cache)

    return build_item(car, deck_type, fuel_data, image_paths)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def generate_index(hh_items, or_items):
    """Generate index.html main menu page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#111">
<title>Swipestack</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#f7f7f7;--card:#fff;--text:#111;--muted:#888;--border:rgba(0,0,0,0.08);}}
@media(prefers-color-scheme:dark){{
  :root{{--bg:#111;--card:#1c1c1e;--text:#eee;--muted:#777;--border:rgba(255,255,255,0.08);}}
}}
html,body{{
  min-height:100%;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--text);-webkit-tap-highlight-color:transparent;
}}
.page{{padding:calc(20px + env(safe-area-inset-top,0px)) 16px 40px;max-width:420px;margin:0 auto;}}
h1{{font-size:28px;font-weight:800;margin-bottom:6px;}}
.subtitle{{font-size:14px;color:var(--muted);margin-bottom:24px;}}
.deck-card{{
  display:flex;align-items:center;gap:14px;
  padding:16px;margin-bottom:12px;
  background:var(--card);border-radius:14px;
  box-shadow:0 1px 8px rgba(0,0,0,0.06);
  text-decoration:none;color:var(--text);
  border:1px solid var(--border);
}}
.deck-card:active{{transform:scale(0.98);}}
.deck-icon{{
  width:52px;height:52px;border-radius:12px;
  background:var(--border);display:flex;align-items:center;justify-content:center;
  flex-shrink:0;
}}
.deck-icon svg{{width:28px;height:28px;fill:var(--text);}}
.deck-info{{flex:1;}}
.deck-name{{font-size:17px;font-weight:700;}}
.deck-count{{font-size:13px;color:var(--muted);}}
.deck-arrow{{fill:var(--muted);}}
</style>
</head>
<body>
<div class="page">
  <h1>Swipestack</h1>
  <div class="subtitle">Comma-compatible cars to swipe through</div>

  <a href="hot_hatches.html" class="deck-card">
    <div class="deck-icon">
      <svg viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.88 0-.33-.75-.31-.78C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.51c.4 0 .62.19.4.66C12.97 17.55 11 21 11 21z"/></svg>
    </div>
    <div class="deck-info">
      <div class="deck-name">Hot Hatches</div>
      <div class="deck-count">{len(hh_items)} cars</div>
    </div>
    <svg class="deck-arrow" viewBox="0 0 24 24" width="20" height="20"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
  </a>

  <a href="off_roaders.html" class="deck-card">
    <div class="deck-icon">
      <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-5.31-7.87l8.18-3.18-3.18 8.18-8.18 3.18 3.18-8.18zM12 11c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/></svg>
    </div>
    <div class="deck-info">
      <div class="deck-name">Off-Roaders</div>
      <div class="deck-count">{len(or_items)} cars</div>
    </div>
    <svg class="deck-arrow" viewBox="0 0 24 24" width="20" height="20"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
  </a>
</div>
</body>
</html>"""
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  -> {OUTPUT_DIR / 'index.html'}")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def main():
    print("Swipestack Car Deck Generator")
    print("=" * 40)

    # Read Excel
    xlsx_path = DATA_DIR / "comma_vehicles.xlsx"
    if not xlsx_path.exists():
        print(f"[!] Excel file not found: {xlsx_path}")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path)
    hot_hatches = consolidate_cars(read_sheet(wb, "Hot Hatches"))
    off_roaders = consolidate_cars(read_sheet(wb, "Off-Roaders"))

    print(f"Hot Hatches: {len(hot_hatches)} models")
    print(f"Off-Roaders: {len(off_roaders)} models")

    # Load cache
    cache = load_cache()

    # Process all cars in parallel
    all_items_hh = []
    all_items_or = []

    print("\nFetching data + images...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures_hh = {
            executor.submit(process_car, car, "hot_hatch", cache): car
            for car in hot_hatches
        }
        futures_or = {
            executor.submit(process_car, car, "off_roader", cache): car
            for car in off_roaders
        }

        for future in as_completed(futures_hh):
            try:
                item = future.result()
                all_items_hh.append(item)
            except Exception as e:
                car = futures_hh[future]
                print(f"  [!] Error processing {car['model']}: {e}")

        for future in as_completed(futures_or):
            try:
                item = future.result()
                all_items_or.append(item)
            except Exception as e:
                car = futures_or[future]
                print(f"  [!] Error processing {car['model']}: {e}")

    # Sort by name
    all_items_hh.sort(key=lambda x: x["name"])
    all_items_or.sort(key=lambda x: x["name"])

    # Save cache
    save_cache(cache)

    # Generate HTML
    print("\nGenerating HTML...")

    hh_path = str(OUTPUT_DIR / "hot_hatches.html")
    swipestack(
        items=all_items_hh,
        output_path=hh_path,
        title="Hot Hatches",
        storage_key="swipestack_hh",
        menu_url="index.html",
    )
    print(f"  -> {hh_path}")

    or_path = str(OUTPUT_DIR / "off_roaders.html")
    swipestack(
        items=all_items_or,
        output_path=or_path,
        title="Off-Roaders",
        storage_key="swipestack_or",
        menu_url="index.html",
    )
    print(f"  -> {or_path}")

    # Generate index.html (main menu)
    generate_index(all_items_hh, all_items_or)

    # Summary
    us_hh = sum(1 for i in all_items_hh if i["region"] == "us")
    eu_hh = sum(1 for i in all_items_hh if i["region"] == "eu")
    us_or = sum(1 for i in all_items_or if i["region"] == "us")
    eu_or = sum(1 for i in all_items_or if i["region"] == "eu")
    total_images = sum(len(i["images"]) for i in all_items_hh + all_items_or)

    ip = get_local_ip()
    port = 8080

    print(f"\n{'=' * 40}")
    print(f"Hot Hatches:  {len(all_items_hh)} cars ({us_hh} US, {eu_hh} EU)")
    print(f"Off-Roaders:  {len(all_items_or)} cars ({us_or} US, {eu_or} EU)")
    print(f"Images:       {total_images} downloaded")
    print(f"\nTo test:")
    print(f"  cd {OUTPUT_DIR} && python3 -m http.server {port}")
    print(f"\nOn this Mac:")
    print(f"  http://localhost:{port}/hot_hatches.html")
    print(f"  http://localhost:{port}/off_roaders.html")
    print(f"\nOn iPhone (same Wi-Fi):")
    print(f"  http://{ip}:{port}/hot_hatches.html")
    print(f"  http://{ip}:{port}/off_roaders.html")

if __name__ == "__main__":
    main()
