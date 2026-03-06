# Swipestack

Tinder-style swipe-to-decide PWA generator. Feed it a list of items with images and stats, get back a self-contained HTML file that works on any phone.

Built for comparing cars (the first use case), but works for apartments, furniture, sneakers, or anything you'd want to swipe through.

## What it does

`swipestack()` takes a list of item dicts and produces a single HTML file with:

- Touch swipe cards with spring-back physics
- Photo carousel per card (tap left/right edges)
- Scrollable stats panel with SVG icons
- Budget filter slider
- US/EU region toggle
- Likes screen with grid view, full profile modal, copy-to-clipboard
- Card counter (3/16)
- Dark mode (system preference)
- Offline PWA support via service worker
- Keyboard shortcuts (arrows + Ctrl+Z undo)

Zero dependencies in the output. No frameworks. One HTML file, relative image paths.

## Quick start

```bash
cd ~/Documents/ventures/swipestack
python3 main.py
cd output && python3 -m http.server 8080
```

Open `http://localhost:8080/index.html` on your phone (same Wi-Fi).

## Module usage

```python
from swipestack import swipestack

items = [
    {
        "id": "item-slug",
        "name": "Item Name",
        "subtitle": "2020-2024",
        "images": ["images/item-slug/front.jpg", "images/item-slug/interior.jpg"],
        "badge": "LABEL" or None,        # small pill badge top-right
        "stats": [
            {"icon": "fuel", "label": "MPG", "value": "28/36", "note": "city/hwy"},
            {"icon": "dollar", "label": "Price", "value": "$18k", "note": "used"},
        ],
        "pros": ["Good thing 1", "Good thing 2"],
        "cons": ["Bad thing 1"],
        "vibe": "One-line description.",
        "footnote": "Optional small text" or None,
        "region": "us",                  # "us" or "eu" for region filter
        "min_price": 18000,              # int, for budget slider filter (0 = no price)
    },
]

swipestack(
    items=items,
    output_path="output/my_deck.html",
    title="My Deck",
    storage_key="my_deck",
    menu_url="index.html",              # optional back button URL
)
```

## Available stat icons

All inline SVG, no emoji anywhere.

`fuel` `gauge` `bolt` `wrench` `engine` `dollar` `drive` `car` `clearance` `tow` `power` `check` `x` `heart` `undo` `info` `compass`

## Car deck (included example)

`main.py` reads `data/comma_vehicles.xlsx` (comma.ai compatible vehicles), fetches MPG data from fueleconomy.gov, downloads images, and generates two swipe decks:

- **Hot Hatches** -- 16 cars (VW GTI, Audi RS3, Kia Stinger, etc.)
- **Off-Roaders** -- 50 cars (RAV4, 4Runner, Bronco Sport, etc.)

### Data sources

- **Vehicle specs**: Hardcoded in `car_data.py` (reliability, 0-60, engine, price range, pros/cons)
- **MPG data**: [fueleconomy.gov REST API](https://www.fueleconomy.gov/feg/ws/) (XML, free, no key needed)
- **Images**: DuckDuckGo image search (see Known Issues below)

## Project structure

```
swipestack.py          # Reusable module: items list -> PWA HTML file
main.py                # Car-specific orchestrator (Excel + API + images -> swipestack())
car_data.py            # Hardcoded vehicle data + fueleconomy.gov model name mapping
data/
  comma_vehicles.xlsx   # Source spreadsheet
output/
  index.html            # Main menu
  hot_hatches.html      # Generated deck
  off_roaders.html      # Generated deck
  sw.js                 # Service worker for offline
  cache.json            # API + image cache (re-run skips cached)
  images/
    volkswagen-golf-gti/
      front.jpg          # Front 3/4 angle
      rear.jpg           # Rear 3/4 angle
      interior.jpg       # Dashboard/cockpit
      side.jpg           # Side profile
```

## Known issues

### Image sourcing is unreliable

DuckDuckGo image search is used because it requires no API key, but it has serious problems:

1. **Rate limiting**: DDG returns 403 on `/i.js` without the `x-vqd-4` header. The current workaround (POST to get vqd token, set header) works but is fragile and could break with any DDG update.

2. **No quality control**: Search results are random. "Front three quarter angle" might return a stock photo, a thumbnail, a modified car, or a completely wrong vehicle. There's no way to verify the image matches the actual car model/year.

3. **Missing angles**: Some queries return no usable results. ~5 out of 66 cars end up with fewer than 4 images.

4. **Speed**: 4 separate DDG searches per car (one per angle) means ~264 HTTP round-trips. With 5 threads this takes 2-3 minutes.

5. **Inconsistency across runs**: Delete cache.json and re-run, you'll get different images. Some better, some worse.

### Better image sources (contributions welcome)

| Source | Pros | Cons |
|--------|------|------|
| **Google Custom Search API** | Higher quality results, filterable | $5/1000 queries, needs API key |
| **Bing Image Search API** | Good quality, supports filters | Paid Azure subscription |
| **Unsplash API** | Free, high quality | Limited car coverage, no specific angles |
| **Car manufacturer press sites** | Official high-res photos, correct angles | Different per OEM, many require login, scraping TOS issues |
| **edmunds.com / cars.com** | Curated per-vehicle galleries with known angles | Requires scraping, TOS issues, layout changes break selectors |
| **Local image directory** | Full control, no API needed | Manual curation effort |

The ideal solution is probably a pluggable image provider interface where `main.py` can use whichever source is configured. The `fetch_images_by_angle()` function already takes structured angle queries -- it just needs a better backend than DDG.

To use your own images, just drop JPGs into `output/images/{slug}/` named `front.jpg`, `rear.jpg`, `interior.jpg`, `side.jpg` and the generator will use them (skips DDG for any car that already has images on disk).

## Dependencies

- Python 3.10+
- `openpyxl` -- Excel reading
- `requests` -- HTTP
- `Pillow` -- Image processing

Installed automatically on first run if missing.

## License

MIT
