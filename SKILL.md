# Swipestack

Generate a Tinder-style swipe-to-decide PWA for any topic. When Oren says "I want a stack for X" or "make me a swipe deck of Y", use this.

## Trigger phrases
- "I want a stack of..."
- "make me a swipe deck"
- "swipestack for..."
- "help me compare..." (when it's a list of items to evaluate)
- "I need to pick between..." (when there are many options)

## Project location
`~/Documents/ventures/swipestack/`

## What to build

A complete swipe deck: research items, fetch images, build stats, generate the PWA HTML. The output is always a self-contained HTML file in `~/Documents/ventures/swipestack/output/`.

## Step-by-step workflow

### 1. Understand the domain

From Oren's request, determine:
- **What items** are being compared (cars, apartments, laptops, sneakers, furniture, etc.)
- **What matters** for this category (price, specs, ratings, location, etc.)
- **What filters** make sense (budget is standard; add domain-specific ones)
- **How many items** — aim for 10-60 for a good swipe session

### 2. Research items

DO NOT fabricate data. For each item, go get real information:
- **Web search** for current specs, prices, reviews
- **APIs** if available (fueleconomy.gov for cars, etc.)
- **Source data** if Oren provides a spreadsheet or list

Build a `{topic}_data.py` file with hardcoded item data, similar to `car_data.py`. Every stat must be real and sourced.

### 3. Fetch images — 5 per item, distinct angles

This is the hardest part and the most important to get right.

**Standard angle set (5 images per item):**

| # | Filename | Search query pattern | Purpose |
|---|----------|---------------------|---------|
| 1 | `front.jpg` | `{item} front three quarter angle` | Hero shot, the "first impression" |
| 2 | `rear.jpg` | `{item} rear three quarter angle` | Back perspective |
| 3 | `interior.jpg` | `{item} interior` / `inside` / `dashboard` | What it's like to use/live with |
| 4 | `detail.jpg` | `{item} detail` / `close up` / domain-specific | Key differentiating feature |
| 5 | `side.jpg` | `{item} side profile` / `full view` | Overall proportions |

Adapt angles per domain:
- **Cars**: front 3/4, rear 3/4, interior dashboard, engine bay or detail, side profile
- **Apartments**: living room, kitchen, bedroom, bathroom, building exterior
- **Furniture**: front view, angled view, detail/texture, in-room context, dimensions overlay
- **Sneakers**: lateral view, medial view, sole, on-foot, box/colorway detail
- **Laptops**: lid closed angled, keyboard top-down, screen on, ports/side, thickness profile

**Image quality rules:**
- Minimum 10KB file size (skip thumbnails)
- Resize to max 800px wide (mobile optimization)
- Save as JPEG quality 82
- Convert to RGB (handle PNGs with transparency)
- Skip duplicate-looking results
- Use `output/images/{slug}/` directory per item

**Image sourcing (in order of preference):**
1. Check if images already exist on disk — skip fetch if so
2. DuckDuckGo image search with `x-vqd-4` header (free, no key)
   - POST to `https://duckduckgo.com` with `data={"q": query}` to get vqd token
   - Set `x-vqd-4` header with the token
   - GET `https://duckduckgo.com/i.js` with params
   - This is FRAGILE — DDG changes their API regularly
3. If DDG fails, note it and move on. The UI handles missing images gracefully.

**One search per angle.** Do NOT use a single generic search for all images — you'll get 5 photos from the same angle.

### 4. Build item dicts

Each item needs this structure:

```python
{
    "id": "unique-slug",           # lowercase, hyphens
    "name": "Display Name",
    "subtitle": "Key differentiator",  # year range, price tier, location, etc.
    "images": ["images/slug/front.jpg", ...],  # relative to output dir
    "badge": "LABEL" or None,      # short tag: "DIESEL", "NEW", "TOP PICK", etc.
    "stats": [                     # 4-8 stats, 2-column grid
        {"icon": "dollar", "label": "Price", "value": "$18k", "note": "used market"},
        {"icon": "gauge", "label": "Rating", "value": "4.5/5", "note": "consumer reports"},
    ],
    "pros": ["Pro 1", "Pro 2", "Pro 3"],   # 2-3 items
    "cons": ["Con 1", "Con 2"],             # 2-3 items
    "vibe": "One sentence personality.",     # italic tagline
    "footnote": "Optional fine print" or None,
    "region": "us",                # for region toggle; "us"/"eu" or skip if N/A
    "min_price": 18000,            # int, for budget slider. 0 = no price data
}
```

### 5. Choose stats + icons per domain

Available icons: `fuel` `gauge` `bolt` `wrench` `engine` `dollar` `drive` `car` `clearance` `tow` `power` `check` `x` `heart` `undo` `info` `compass`

Pick 4-8 stats that matter for the domain. Examples:

**Cars:** MPG, 0-60, engine, power, drive, price, reliability, fun factor
**Apartments:** rent, sqft, commute time, walk score, parking, pet policy
**Laptops:** price, battery life, weight, screen size, storage, CPU score
**Sneakers:** retail price, resale value, weight, drop (heel-toe), colorways, release date
**Furniture:** price, dimensions, material, weight capacity, assembly, warranty

### 6. Define filters

**Budget slider is always included** if items have prices. Set `min_price` on each item.

For domain-specific filters, use the `region` field creatively:
- Cars: "us" / "eu" for availability
- Apartments: "1br" / "2br" for bedroom count
- Or just set everything to "us" and hide the toggle if not needed

### 7. Generate the deck

```python
import sys
sys.path.insert(0, str(Path.home() / "Documents/ventures/swipestack"))
from swipestack import swipestack

swipestack(
    items=items_list,
    output_path=str(Path.home() / "Documents/ventures/swipestack/output/my_deck.html"),
    title="Deck Title",
    storage_key="unique_key",      # localStorage namespace, no spaces
    menu_url="index.html",         # back to main menu
)
```

### 8. Update the index

Add the new deck to `output/index.html` so it appears in the main menu. Read the existing file and add a new `deck-card` link.

### 9. Verify

- Run `python3 -m http.server 8080` in the output dir
- `curl` the HTML to confirm it loads
- Check zero emojis in the output
- Confirm image count per item
- Test budget slider range makes sense

## UI spec (already built into swipestack.py)

- Monochrome design — no color accents, all black/white/gray
- Card stack: 52% photo area, 48% scrollable profile panel
- Photo carousel: tap left/right edges, dot indicators, instant switch (no fade)
- Bottom bar: 44px pass/like buttons, 36px undo, compact 52px bar
- Budget slider below header
- Card counter "3/16" in header
- Likes screen with grid + copy list + start over
- Dark mode via `prefers-color-scheme`
- PWA with offline support via `sw.js`
- All icons are inline SVG — zero emojis anywhere

## File structure for a new deck

```
~/Documents/ventures/swipestack/
  {topic}_data.py              # hardcoded item data for the new domain
  output/
    {topic}.html               # generated deck
    index.html                 # updated with new deck link
    images/
      {item-slug}/
        front.jpg
        rear.jpg
        interior.jpg
        detail.jpg
        side.jpg
```

## Reference

- Module: `~/Documents/ventures/swipestack/swipestack.py`
- Car example: `~/Documents/ventures/swipestack/main.py` + `car_data.py`
- Repo: `https://github.com/orenmendelow/swipestack`
