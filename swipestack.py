"""
swipestack — generates a Tinder-style swipe-to-decide PWA as a single HTML file.
"""

import json
from pathlib import Path


def swipestack(
    items: list[dict],
    output_path: str,
    title: str,
    accent_color: str = "#888",
    storage_key: str = "swipestack",
    menu_url: str | None = None,
):
    items_json = json.dumps(items)
    menu_btn_html = ""
    if menu_url:
        menu_btn_html = f'<a href="{menu_url}" class="menu-btn"><svg viewBox="0 0 24 24" width="20" height="20"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg></a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#111">
<title>{title}</title>
<link rel="manifest" href='data:application/json,{json.dumps({"name": title, "short_name": title, "start_url": ".", "display": "standalone", "background_color": "#111", "theme_color": "#111"})}'>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#f7f7f7;--card-bg:#fff;--text:#111;--text-muted:#888;
  --panel-bg:rgba(255,255,255,0.92);--header-bg:rgba(255,255,255,0.95);
  --divider:rgba(0,0,0,0.08);--icon-fill:#666;
  --pass-bg:#e5e5e5;--pass-fg:#555;--like-bg:#333;--like-fg:#fff;
  --badge-bg:#555;--badge-fg:#fff;
  --pro:#444;--con:#999;
}}
@media(prefers-color-scheme:dark){{
  :root{{
    --bg:#111;--card-bg:#1c1c1e;--text:#eee;--text-muted:#777;
    --panel-bg:rgba(28,28,30,0.92);--header-bg:rgba(17,17,17,0.95);
    --divider:rgba(255,255,255,0.08);--icon-fill:#999;
    --pass-bg:#333;--pass-fg:#bbb;--like-bg:#ddd;--like-fg:#111;
    --badge-bg:#aaa;--badge-fg:#111;
    --pro:#ccc;--con:#666;
  }}
}}
html,body{{
  height:100%;width:100%;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--text);
  -webkit-tap-highlight-color:transparent;
  user-select:none;-webkit-user-select:none;
}}

.header{{position:fixed;top:0;left:0;right:0;z-index:100;padding-top:env(safe-area-inset-top,0px);}}
.header-inner{{
  display:flex;align-items:center;justify-content:space-between;
  height:48px;padding:0 12px;
  background:var(--header-bg);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--divider);
}}
.header-left{{display:flex;align-items:center;gap:8px;}}
.menu-btn{{display:flex;align-items:center;padding:4px;text-decoration:none;}}
.menu-btn svg{{fill:var(--text);}}
.header-title{{font-size:17px;font-weight:700;}}
.header-right{{display:flex;align-items:center;gap:10px;}}
.counter{{font-size:12px;color:var(--text-muted);font-weight:600;font-variant-numeric:tabular-nums;}}
.likes-btn{{
  display:flex;align-items:center;gap:3px;
  background:none;border:none;color:var(--text);cursor:pointer;
  font-size:14px;font-weight:600;padding:4px;
}}
.likes-btn svg{{width:18px;height:18px;fill:var(--text);}}
.region-toggle{{
  display:flex;border-radius:12px;overflow:hidden;
  border:1px solid var(--divider);
}}
.region-toggle button{{
  padding:3px 10px;font-size:11px;font-weight:600;
  border:none;cursor:pointer;background:transparent;color:var(--text-muted);
}}
.region-toggle button.active{{background:var(--text);color:var(--bg);border-radius:11px;}}

.budget-bar{{
  position:fixed;top:calc(48px + env(safe-area-inset-top,0px));left:0;right:0;z-index:99;
  padding:6px 12px;display:flex;align-items:center;gap:8px;
  background:var(--header-bg);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--divider);
  font-size:12px;color:var(--text-muted);
}}
.budget-bar label{{font-weight:600;white-space:nowrap;}}
.budget-bar input[type=range]{{flex:1;accent-color:var(--text);height:20px;}}
.budget-val{{font-weight:700;color:var(--text);min-width:40px;text-align:right;font-variant-numeric:tabular-nums;}}

.main{{
  position:fixed;
  top:calc(48px + 34px + env(safe-area-inset-top,0px));
  bottom:calc(56px + env(safe-area-inset-bottom,0px));
  left:0;right:0;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}}

.card-container{{position:relative;width:100%;height:100%;max-width:420px;}}
.card{{
  position:absolute;top:4px;left:6px;right:6px;bottom:4px;
  border-radius:14px;overflow:hidden;
  background:var(--card-bg);
  box-shadow:0 2px 16px rgba(0,0,0,0.1);
  display:flex;flex-direction:column;
  transform-origin:center center;
  will-change:transform;
  touch-action:none;
}}
.card.active{{z-index:3;}}
.card.next{{z-index:2;transform:scale(0.97) translateY(6px);pointer-events:none;}}
.card.third{{z-index:1;transform:scale(0.94) translateY(12px);pointer-events:none;}}
.card.entering{{animation:cardEnter .2s ease-out;}}
@keyframes cardEnter{{from{{transform:scale(0.95);opacity:0.7}}to{{transform:scale(1);opacity:1}}}}
.card.swiping-right .stamp-like,.card.swiping-left .stamp-nope{{opacity:1;}}

.stamp{{
  position:absolute;top:20%;left:50%;transform:translate(-50%,-50%);
  z-index:20;font-size:40px;font-weight:900;letter-spacing:2px;
  padding:6px 20px;border-radius:10px;
  border:3px solid;opacity:0;pointer-events:none;
}}
.stamp-like{{color:#333;border-color:#333;transform:translate(-50%,-50%) rotate(-15deg);}}
.stamp-nope{{color:#999;border-color:#999;transform:translate(-50%,-50%) rotate(15deg);}}
@media(prefers-color-scheme:dark){{
  .stamp-like{{color:#ddd;border-color:#ddd;}}
  .stamp-nope{{color:#666;border-color:#666;}}
}}

.card-images{{position:relative;flex:0 0 52%;overflow:hidden;background:#222;}}
.card-images img{{
  position:absolute;top:0;left:0;width:100%;height:100%;
  object-fit:cover;display:none;
}}
.card-images img.visible{{display:block;}}
.img-placeholder{{
  display:flex;align-items:center;justify-content:center;
  width:100%;height:100%;
}}
.img-placeholder svg{{width:48px;height:48px;fill:var(--text-muted);opacity:.2;}}
.img-dots{{
  position:absolute;bottom:6px;left:50%;transform:translateX(-50%);
  display:flex;gap:4px;z-index:10;
}}
.img-dots span{{
  width:6px;height:6px;border-radius:50%;
  background:rgba(255,255,255,0.35);
}}
.img-dots span.active{{background:#fff;transform:scale(1.2);}}
.img-tap-zone{{position:absolute;top:0;bottom:0;z-index:5;}}
.img-tap-zone.left{{left:0;width:30%;}}
.img-tap-zone.right{{right:0;width:30%;}}

.card-profile{{
  flex:1;overflow-y:auto;overflow-x:hidden;
  -webkit-overflow-scrolling:touch;
  padding:12px 14px 16px;
  background:var(--panel-bg);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-radius:14px 14px 0 0;
  margin-top:-14px;position:relative;z-index:5;
}}
.card-badge{{
  position:absolute;top:10px;right:14px;
  display:inline-flex;align-items:center;gap:3px;
  background:var(--badge-bg);color:var(--badge-fg);
  font-size:10px;font-weight:700;letter-spacing:.5px;
  padding:2px 8px;border-radius:10px;
}}
.card-badge svg{{width:12px;height:12px;fill:var(--badge-fg);}}
.card-name{{font-size:20px;font-weight:800;margin-bottom:1px;padding-right:70px;line-height:1.2;}}
.card-subtitle{{font-size:13px;color:var(--text-muted);margin-bottom:10px;}}

.stats-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;}}
.stat{{
  display:flex;align-items:flex-start;gap:6px;
  padding:5px 7px;border-radius:7px;background:var(--divider);
}}
.stat svg{{width:15px;height:15px;flex-shrink:0;margin-top:1px;fill:var(--icon-fill);}}
.stat-text{{display:flex;flex-direction:column;}}
.stat-label{{font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.3px;}}
.stat-value{{font-size:13px;font-weight:700;line-height:1.2;}}
.stat-note{{font-size:9px;color:var(--text-muted);}}

.pros-cons{{margin-bottom:8px;}}
.pros-cons ul{{list-style:none;padding:0;}}
.pros-cons li{{display:flex;align-items:flex-start;gap:5px;font-size:12px;line-height:1.3;margin-bottom:3px;}}
.pros-cons li svg{{width:14px;height:14px;flex-shrink:0;margin-top:1px;}}
.pros-cons .pro svg{{fill:var(--pro);}}
.pros-cons .con svg{{fill:var(--con);}}
.card-vibe{{font-size:12px;font-style:italic;color:var(--text-muted);margin-bottom:4px;}}
.card-footnote{{
  font-size:11px;color:var(--text-muted);
  border-top:1px solid var(--divider);
  padding-top:6px;margin-top:6px;
}}

.bottom-bar{{
  position:fixed;bottom:0;left:0;right:0;z-index:100;
  padding-bottom:env(safe-area-inset-bottom,0px);
  background:var(--header-bg);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-top:1px solid var(--divider);
}}
.bottom-bar-inner{{
  display:flex;align-items:center;justify-content:center;gap:28px;
  height:52px;max-width:420px;margin:0 auto;
}}
.action-btn{{
  display:flex;align-items:center;justify-content:center;
  border:none;border-radius:50%;cursor:pointer;
  transition:transform .1s;
}}
.action-btn:active{{transform:scale(0.9);}}
.btn-pass{{
  width:44px;height:44px;
  background:var(--pass-bg);color:var(--pass-fg);
  border:1.5px solid var(--divider);
}}
.btn-pass svg{{width:20px;height:20px;fill:var(--pass-fg);}}
.btn-undo{{width:36px;height:36px;background:transparent;border:1.5px solid var(--divider);}}
.btn-undo svg{{width:16px;height:16px;fill:var(--text-muted);}}
.btn-like{{
  width:44px;height:44px;
  background:var(--like-bg);color:var(--like-fg);
}}
.btn-like svg{{width:20px;height:20px;fill:var(--like-fg);}}

.likes-screen{{
  position:fixed;inset:0;z-index:200;background:var(--bg);
  display:none;flex-direction:column;
}}
.likes-screen.visible{{display:flex;}}
.likes-header{{
  display:flex;align-items:center;gap:10px;
  padding:10px 12px;padding-top:calc(10px + env(safe-area-inset-top,0px));
  border-bottom:1px solid var(--divider);
  background:var(--header-bg);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
}}
.likes-back{{
  background:none;border:none;color:var(--text);
  font-size:14px;font-weight:600;cursor:pointer;
  display:flex;align-items:center;gap:3px;
}}
.likes-back svg{{width:18px;height:18px;fill:var(--text);}}
.likes-header-title{{font-size:17px;font-weight:700;flex:1;}}
.likes-actions{{display:flex;gap:6px;}}
.likes-actions button{{
  padding:5px 12px;border-radius:16px;border:1px solid var(--divider);
  font-size:12px;font-weight:600;cursor:pointer;
  background:var(--bg);color:var(--text);
}}
.btn-copy{{background:var(--text)!important;color:var(--bg)!important;border-color:var(--text)!important;}}
.likes-grid{{
  flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;
  padding:10px;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;
}}
.likes-grid-item{{
  border-radius:10px;overflow:hidden;cursor:pointer;
  aspect-ratio:3/4;position:relative;background:var(--card-bg);
  box-shadow:0 1px 6px rgba(0,0,0,0.06);
}}
.likes-grid-item img{{width:100%;height:100%;object-fit:cover;}}
.likes-grid-item .likes-item-name{{
  position:absolute;bottom:0;left:0;right:0;
  padding:20px 6px 6px;
  background:linear-gradient(transparent,rgba(0,0,0,0.65));
  color:#fff;font-size:12px;font-weight:600;
}}
.likes-empty{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  flex:1;color:var(--text-muted);gap:6px;font-size:14px;
}}
.likes-empty svg{{width:40px;height:40px;fill:var(--text-muted);opacity:.2;}}

.modal-overlay{{
  position:fixed;inset:0;z-index:300;
  background:rgba(0,0,0,0.5);
  display:none;align-items:flex-end;justify-content:center;
}}
.modal-overlay.visible{{display:flex;}}
.modal{{
  width:100%;max-width:420px;max-height:85vh;
  background:var(--card-bg);border-radius:16px 16px 0 0;
  overflow-y:auto;-webkit-overflow-scrolling:touch;
  padding:16px 14px calc(16px + env(safe-area-inset-bottom,0px));
}}
.modal-close{{
  display:flex;align-items:center;gap:3px;
  background:none;border:none;color:var(--text);
  font-size:14px;font-weight:600;cursor:pointer;margin-bottom:10px;
}}
.modal-close svg{{width:16px;height:16px;fill:var(--text);}}
.modal .card-images{{position:relative;height:220px;border-radius:10px;overflow:hidden;margin-bottom:14px;flex:none;}}

.end-screen{{
  display:none;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;gap:14px;padding:28px;
  position:absolute;inset:0;
}}
.end-screen.visible{{display:flex;}}
.end-screen h2{{font-size:20px;font-weight:700;}}
.end-screen p{{color:var(--text-muted);font-size:14px;}}
.end-screen button{{
  padding:10px 24px;border-radius:50px;border:none;
  font-size:14px;font-weight:700;cursor:pointer;
}}
.end-btn-likes{{background:var(--text);color:var(--bg);}}
.end-btn-reset{{background:var(--divider);color:var(--text);}}
</style>
</head>
<body>

<div class="header">
<div class="header-inner">
  <div class="header-left">
    {menu_btn_html}
    <div class="header-title">{title}</div>
  </div>
  <div class="header-right">
    <span class="counter" id="counter"></span>
    <div class="region-toggle">
      <button id="regionUs" class="active" onclick="setRegion('us')">US</button>
      <button id="regionAll" onclick="setRegion('all')">All</button>
    </div>
    <button class="likes-btn" id="likesBtn" onclick="showLikes()">
      <span class="likes-count" id="likesCount">0</span>
      <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
    </button>
  </div>
</div>
</div>

<div class="budget-bar">
  <label>Budget</label>
  <input type="range" id="budgetSlider" min="0" max="100" value="100" oninput="onBudget(this.value)">
  <span class="budget-val" id="budgetVal">Any</span>
</div>

<div class="main">
  <div class="card-container" id="cardContainer"></div>
  <div class="end-screen" id="endScreen">
    <h2 id="endTitle">Done!</h2>
    <p id="endSub"></p>
    <button class="end-btn-likes" onclick="showLikes()">Review Likes</button>
    <button class="end-btn-reset" onclick="startOver()">Start Over</button>
  </div>
</div>

<div class="bottom-bar">
<div class="bottom-bar-inner">
  <button class="action-btn btn-pass" onclick="doPass()">
    <svg viewBox="0 0 24 24"><path d="M18.3 5.71a1 1 0 00-1.41 0L12 10.59 7.11 5.7A1 1 0 105.7 7.11L10.59 12 5.7 16.89a1 1 0 101.41 1.41L12 13.41l4.89 4.89a1 1 0 001.41-1.41L13.41 12l4.89-4.89a1 1 0 000-1.4z"/></svg>
  </button>
  <button class="action-btn btn-undo" onclick="doUndo()">
    <svg viewBox="0 0 24 24"><path d="M12.5 8c-2.65 0-5.05 1.04-6.83 2.73L2.5 7.5v9h9l-3.19-3.19C9.76 12.07 11.07 11.5 12.5 11.5c3.03 0 5.55 2.12 6.2 4.97l2.93-.82C20.6 11.37 16.9 8 12.5 8z"/></svg>
  </button>
  <button class="action-btn btn-like" onclick="doLike()">
    <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
  </button>
</div>
</div>

<div class="likes-screen" id="likesScreen">
<div class="likes-header">
  <button class="likes-back" onclick="hideLikes()">
    <svg viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
    Back
  </button>
  <div class="likes-header-title">Liked</div>
  <div class="likes-actions">
    <button class="btn-copy" onclick="copyLikes()">Copy List</button>
    <button onclick="startOver()">Start Over</button>
  </div>
</div>
<div class="likes-grid" id="likesGrid"></div>
</div>

<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
<div class="modal" id="modal" onclick="event.stopPropagation()"></div>
</div>

<script>
const ITEMS = {items_json};
const STORAGE_KEY = "{storage_key}";

const ICONS = {{
  fuel:'<svg viewBox="0 0 24 24"><path d="M19.77 7.23l.01-.01-3.72-3.72L14.65 4.9l2.5 2.5c-.95.4-1.62 1.33-1.62 2.42 0 1.45 1.18 2.63 2.63 2.63.34 0 .66-.07.96-.18V18c0 .55-.45 1-1 1s-1-.45-1-1v-3c0-1.1-.9-2-2-2h-1V5c0-1.1-.9-2-2-2H6C4.9 3 4 3.9 4 5v14c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2v-5h1v3c0 1.66 1.34 3 3 3s3-1.34 3-3V9c0-.69-.28-1.32-.73-1.77zM12 10H6V5h6v5z"/></svg>',
  gauge:'<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm4.24-12.24L11 13l-1.41-1.41a2 2 0 10-2.83 2.83l2.83 2.83a2 2 0 002.82 0l6.24-6.24a2 2 0 00-2.83-2.83l-.58.58z"/></svg>',
  bolt:'<svg viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.88 0-.33-.75-.31-.78C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.51c.4 0 .62.19.4.66C12.97 17.55 11 21 11 21z"/></svg>',
  wrench:'<svg viewBox="0 0 24 24"><path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/></svg>',
  engine:'<svg viewBox="0 0 24 24"><path d="M7 4v2h3v2H4c-1.1 0-2 .9-2 2v5c0 1.1.9 2 2 2h1v3h2v-3h6v3h2v-3h1c1.1 0 2-.9 2-2v-1h2v-4h-2V10c0-1.1-.9-2-2-2h-3V6h3V4H7zm9 6v5H6v-5h10z"/></svg>',
  dollar:'<svg viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>',
  drive:'<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-12c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>',
  car:'<svg viewBox="0 0 24 24"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>',
  clearance:'<svg viewBox="0 0 24 24"><path d="M5 20h14v-2H5v2zm7-18L2 8l2 2 8-5 8 5 2-2-10-6zm0 6L7.5 11 6 12l6 4 6-4-1.5-1L12 8z"/></svg>',
  tow:'<svg viewBox="0 0 24 24"><path d="M18 18h-1V7.17c0-.53-.21-1.04-.59-1.41L12.83 2.17 11.42 3.58 15 7.17V18H9V7.17L12.58 3.58 11.17 2.17 7.59 5.76C7.21 6.13 7 6.64 7 7.17V18H6c-.55 0-1 .45-1 1s.45 1 1 1h12c.55 0 1-.45 1-1s-.45-1-1-1z"/></svg>',
  power:'<svg viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.88 0-.33-.75-.31-.78C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.51c.4 0 .62.19.4.66C12.97 17.55 11 21 11 21z"/></svg>',
  check:'<svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>',
  x:'<svg viewBox="0 0 24 24"><path d="M18.3 5.71a1 1 0 00-1.41 0L12 10.59 7.11 5.7A1 1 0 105.7 7.11L10.59 12 5.7 16.89a1 1 0 101.41 1.41L12 13.41l4.89 4.89a1 1 0 001.41-1.41L13.41 12l4.89-4.89a1 1 0 000-1.4z"/></svg>',
  heart:'<svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>',
  undo:'<svg viewBox="0 0 24 24"><path d="M12.5 8c-2.65 0-5.05 1.04-6.83 2.73L2.5 7.5v9h9l-3.19-3.19C9.76 12.07 11.07 11.5 12.5 11.5c3.03 0 5.55 2.12 6.2 4.97l2.93-.82C20.6 11.37 16.9 8 12.5 8z"/></svg>',
  info:'<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
  compass:'<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-5.31-7.87l8.18-3.18-3.18 8.18-8.18 3.18 3.18-8.18zM12 11c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/></svg>',
}};

function getIcon(name) {{ return ICONS[name] || ICONS.info; }}

let allItems = [...ITEMS];
let deck = [];
let likes = JSON.parse(localStorage.getItem(STORAGE_KEY+'_likes')||'[]');
let seen = JSON.parse(localStorage.getItem(STORAGE_KEY+'_seen')||'[]');
let region = localStorage.getItem(STORAGE_KEY+'_region')||'us';
let budget = parseInt(localStorage.getItem(STORAGE_KEY+'_budget')||'0',10)||0; // 0 = no limit
let history = [];
let swiping = false;
let startX=0,startY=0,currentX=0,isDragging=false,isScrolling=false;
let imgTouchStartX=0,imgTouchStartY=0,imgIsDragging=false,imgSwipeActive=false;

function save() {{
  localStorage.setItem(STORAGE_KEY+'_likes',JSON.stringify(likes));
  localStorage.setItem(STORAGE_KEY+'_seen',JSON.stringify(seen));
  localStorage.setItem(STORAGE_KEY+'_region',region);
  if(budget>0) localStorage.setItem(STORAGE_KEY+'_budget',budget);
  else localStorage.removeItem(STORAGE_KEY+'_budget');
  document.getElementById('likesCount').textContent=likes.length;
}}

function getFilteredItems() {{
  let items=allItems;
  if(region==='us') items=items.filter(i=>i.region!=='eu');
  if(budget>0) items=items.filter(i=>!i.min_price||i.min_price<=budget);
  return items;
}}

function buildDeck() {{
  const filtered=getFilteredItems();
  deck=filtered.filter(i=>!seen.includes(i.id));
  renderCards();
  updateCounter();
  updateEndScreen();
}}

function updateCounter() {{
  const filtered=getFilteredItems();
  const remaining=deck.length;
  const total=filtered.length;
  const el=document.getElementById('counter');
  if(total>0) el.textContent=(total-remaining+1>total?total:total-remaining+1)+'/'+total;
  else el.textContent='';
}}

function updateEndScreen() {{
  const container=document.getElementById('cardContainer');
  const end=document.getElementById('endScreen');
  if(deck.length===0) {{
    container.innerHTML='';
    const total=getFilteredItems().length;
    document.getElementById('endTitle').textContent="All "+total+" cars reviewed";
    document.getElementById('endSub').textContent=likes.length+" liked";
    end.classList.add('visible');
  }} else {{
    end.classList.remove('visible');
  }}
}}

/* BUDGET */
function initBudget() {{
  const prices=allItems.map(i=>i.min_price||0).filter(p=>p>0);
  if(prices.length===0) return;
  const maxP=Math.max(...prices);
  const slider=document.getElementById('budgetSlider');
  // Slider from 5k to max price in 5k steps, plus 0=any
  const step=5000;
  const maxVal=Math.ceil(maxP/step)*step;
  slider.min=0;
  slider.max=maxVal;
  slider.step=step;
  slider.value=budget>0?budget:maxVal;
  updateBudgetLabel(budget>0?budget:0);
}}
function onBudget(val) {{
  val=parseInt(val,10);
  const slider=document.getElementById('budgetSlider');
  const maxVal=parseInt(slider.max,10);
  if(val>=maxVal) {{
    budget=0;
    updateBudgetLabel(0);
  }} else {{
    budget=val;
    updateBudgetLabel(val);
  }}
  save();
  buildDeck();
}}
function updateBudgetLabel(val) {{
  const el=document.getElementById('budgetVal');
  if(val<=0) el.textContent='Any';
  else if(val>=1000) el.textContent='$'+Math.round(val/1000)+'k';
  else el.textContent='$'+val;
}}

/* REGION */
function setRegion(r) {{
  region=r;
  document.getElementById('regionUs').classList.toggle('active',r==='us');
  document.getElementById('regionAll').classList.toggle('active',r==='all');
  save();buildDeck();
}}

/* CARD RENDERING */
function renderCards() {{
  const container=document.getElementById('cardContainer');
  container.innerHTML='';
  if(deck.length===0) return;
  const max=Math.min(deck.length,3);
  for(let i=max-1;i>=0;i--) container.appendChild(createCard(deck[i],i));
}}

function createCard(item,stackIndex) {{
  const card=document.createElement('div');
  card.className='card'+(stackIndex===0?' active entering':stackIndex===1?' next':' third');
  card.dataset.id=item.id;
  card.innerHTML='<div class="stamp stamp-like">LIKE</div><div class="stamp stamp-nope">NOPE</div>';

  const imgArea=document.createElement('div');
  imgArea.className='card-images';
  if(item.images&&item.images.length>0) {{
    item.images.forEach((src,idx)=>{{
      const img=document.createElement('img');
      img.src=src;img.alt=item.name;
      img.loading=idx<2?'eager':'lazy';
      if(idx===0) img.classList.add('visible');
      imgArea.appendChild(img);
    }});
    if(item.images.length>1) {{
      const dots=document.createElement('div');
      dots.className='img-dots';
      item.images.forEach((_,idx)=>{{
        const d=document.createElement('span');
        if(idx===0) d.classList.add('active');
        dots.appendChild(d);
      }});
      imgArea.appendChild(dots);
      const tapL=document.createElement('div');
      tapL.className='img-tap-zone left';
      tapL.addEventListener('click',e=>{{e.stopPropagation();changeImg(card,-1);}});
      imgArea.appendChild(tapL);
      const tapR=document.createElement('div');
      tapR.className='img-tap-zone right';
      tapR.addEventListener('click',e=>{{e.stopPropagation();changeImg(card,1);}});
      imgArea.appendChild(tapR);
    }}
  }} else {{
    imgArea.innerHTML='<div class="img-placeholder">'+ICONS.car+'</div>';
  }}
  card.appendChild(imgArea);

  const profile=document.createElement('div');
  profile.className='card-profile';
  let h='';
  if(item.badge) h+='<div class="card-badge">'+getIcon('fuel')+' '+esc(item.badge)+'</div>';
  h+='<div class="card-name">'+esc(item.name)+'</div>';
  h+='<div class="card-subtitle">'+esc(item.subtitle)+'</div>';
  if(item.stats&&item.stats.length>0) {{
    h+='<div class="stats-grid">';
    item.stats.forEach(s=>{{
      h+='<div class="stat">'+getIcon(s.icon)+'<div class="stat-text"><span class="stat-label">'+esc(s.label)+'</span><span class="stat-value">'+esc(s.value)+'</span>'+(s.note?'<span class="stat-note">'+esc(s.note)+'</span>':'')+'</div></div>';
    }});
    h+='</div>';
  }}
  if((item.pros&&item.pros.length)||(item.cons&&item.cons.length)) {{
    h+='<div class="pros-cons">';
    if(item.pros) {{h+='<ul>';item.pros.forEach(p=>{{h+='<li class="pro">'+ICONS.check+' '+esc(p)+'</li>';}});h+='</ul>';}}
    if(item.cons) {{h+='<ul>';item.cons.forEach(c=>{{h+='<li class="con">'+ICONS.x+' '+esc(c)+'</li>';}});h+='</ul>';}}
    h+='</div>';
  }}
  if(item.vibe) h+='<div class="card-vibe">'+esc(item.vibe)+'</div>';
  if(item.footnote) h+='<div class="card-footnote">'+esc(item.footnote)+'</div>';
  profile.innerHTML=h;
  card.appendChild(profile);

  if(stackIndex===0) {{setupSwipe(card);card._imgIndex=0;}}
  return card;
}}

function esc(s) {{if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML;}}

function changeImg(card,dir) {{
  const imgs=card.querySelectorAll('.card-images img');
  const dots=card.querySelectorAll('.img-dots span');
  if(imgs.length<2) return;
  let idx=(card._imgIndex||0)+dir;
  if(idx<0)idx=0;if(idx>=imgs.length)idx=imgs.length-1;
  card._imgIndex=idx;
  imgs.forEach((img,i)=>img.classList.toggle('visible',i===idx));
  dots.forEach((d,i)=>d.classList.toggle('active',i===idx));
}}

/* SWIPE */
function setupSwipe(card) {{
  const imgArea=card.querySelector('.card-images');
  imgArea.addEventListener('touchstart',onImgTouchStart,{{passive:true}});
  imgArea.addEventListener('touchmove',onImgTouchMove,{{passive:false}});
  imgArea.addEventListener('touchend',onImgTouchEnd,{{passive:true}});
  card.addEventListener('touchstart',onTouchStart,{{passive:true}});
  card.addEventListener('touchmove',onTouchMove,{{passive:false}});
  card.addEventListener('touchend',onTouchEnd,{{passive:true}});
  card.addEventListener('mousedown',onMouseDown);
}}

function onImgTouchStart(e) {{imgTouchStartX=e.touches[0].clientX;imgTouchStartY=e.touches[0].clientY;imgIsDragging=false;imgSwipeActive=false;}}
function onImgTouchMove(e) {{
  const dx=e.touches[0].clientX-imgTouchStartX;
  const dy=e.touches[0].clientY-imgTouchStartY;
  if(!imgIsDragging) {{if(Math.abs(dx)>8&&Math.abs(dx)>Math.abs(dy)*1.5){{imgIsDragging=true;imgSwipeActive=true;e.preventDefault();}}}}
  else e.preventDefault();
}}
function onImgTouchEnd(e) {{
  if(imgIsDragging) {{
    const dx=e.changedTouches[0].clientX-imgTouchStartX;
    const card=e.currentTarget.closest('.card');
    if(Math.abs(dx)>30) changeImg(card,dx<0?1:-1);
    imgIsDragging=false;
    setTimeout(()=>{{imgSwipeActive=false;}},50);
  }}
}}

function onTouchStart(e) {{
  if(swiping||imgSwipeActive) return;
  startX=e.touches[0].clientX;startY=e.touches[0].clientY;
  isDragging=false;isScrolling=false;currentX=0;
}}
function onTouchMove(e) {{
  if(swiping||imgSwipeActive) return;
  const dx=e.touches[0].clientX-startX;
  const dy=e.touches[0].clientY-startY;
  if(!isDragging&&!isScrolling) {{
    if(Math.abs(dy)>Math.abs(dx)&&Math.abs(dy)>8){{isScrolling=true;return;}}
    if(Math.abs(dx)>8) isDragging=true;
  }}
  if(isScrolling||!isDragging) return;
  e.preventDefault();
  currentX=dx;
  const card=e.currentTarget;
  card.style.transition='none';
  card.style.transform='translateX('+dx+'px) rotate('+(dx*0.05)+'deg)';
  card.classList.toggle('swiping-right',dx>40);
  card.classList.toggle('swiping-left',dx<-40);
}}
function onTouchEnd(e) {{
  if(swiping||isScrolling||imgSwipeActive||!isDragging) return;
  isDragging=false;
  const card=e.currentTarget;
  const threshold=window.innerWidth*0.35;
  if(Math.abs(currentX)>threshold) commitSwipe(card,currentX>0?'right':'left');
  else springBack(card);
}}

let mouseCard=null;
function onMouseDown(e) {{
  if(swiping||e.target.closest('button,a,.img-tap-zone')) return;
  mouseCard=e.currentTarget;startX=e.clientX;currentX=0;isDragging=false;
  document.addEventListener('mousemove',onMouseMove);
  document.addEventListener('mouseup',onMouseUp);
}}
function onMouseMove(e) {{
  if(!mouseCard||swiping) return;
  const dx=e.clientX-startX;
  if(!isDragging&&Math.abs(dx)>5) isDragging=true;
  if(!isDragging) return;
  currentX=dx;
  mouseCard.style.transition='none';
  mouseCard.style.transform='translateX('+dx+'px) rotate('+(dx*0.05)+'deg)';
  mouseCard.classList.toggle('swiping-right',dx>40);
  mouseCard.classList.toggle('swiping-left',dx<-40);
}}
function onMouseUp() {{
  document.removeEventListener('mousemove',onMouseMove);
  document.removeEventListener('mouseup',onMouseUp);
  if(!mouseCard||!isDragging){{mouseCard=null;return;}}
  const threshold=window.innerWidth*0.35;
  if(Math.abs(currentX)>threshold) commitSwipe(mouseCard,currentX>0?'right':'left');
  else springBack(mouseCard);
  mouseCard=null;isDragging=false;
}}

function springBack(card) {{
  card.style.transition='transform .25s cubic-bezier(0.175,0.885,0.32,1.275)';
  card.style.transform='';
  card.classList.remove('swiping-right','swiping-left');
}}

function commitSwipe(card,dir) {{
  swiping=true;
  const offX=dir==='right'?window.innerWidth*1.5:-window.innerWidth*1.5;
  card.style.transition='transform .25s ease-out';
  card.style.transform='translateX('+offX+'px) rotate('+(offX*0.04)+'deg)';
  card.classList.add(dir==='right'?'swiping-right':'swiping-left');
  const id=card.dataset.id;
  const action=dir==='right'?'like':'pass';
  setTimeout(()=>{{
    if(action==='like'&&!likes.includes(id)) likes.push(id);
    if(!seen.includes(id)) seen.push(id);
    history.push({{id:id,action:action}});
    save();deck.shift();renderCards();updateCounter();updateEndScreen();swiping=false;
  }},250);
}}

function doPass() {{const c=document.querySelector('.card.active');if(c&&!swiping) commitSwipe(c,'left');}}
function doLike() {{const c=document.querySelector('.card.active');if(c&&!swiping) commitSwipe(c,'right');}}
function doUndo() {{
  if(history.length===0||swiping) return;
  const last=history.pop();
  seen=seen.filter(id=>id!==last.id);
  if(last.action==='like') likes=likes.filter(id=>id!==last.id);
  save();buildDeck();
}}

document.addEventListener('keydown',e=>{{
  if(document.getElementById('likesScreen').classList.contains('visible')) return;
  if(document.getElementById('modalOverlay').classList.contains('visible')) return;
  if(e.key==='ArrowLeft') doPass();
  if(e.key==='ArrowRight') doLike();
  if((e.ctrlKey||e.metaKey)&&e.key==='z') doUndo();
}});

function showLikes() {{
  const grid=document.getElementById('likesGrid');
  grid.innerHTML='';
  if(likes.length===0) {{
    grid.innerHTML='<div class="likes-empty">'+ICONS.heart+'<div>No likes yet</div></div>';
  }} else {{
    likes.forEach(id=>{{
      const item=allItems.find(i=>i.id===id);if(!item) return;
      const el=document.createElement('div');el.className='likes-grid-item';
      el.onclick=()=>showModal(item);
      const thumb=(item.images&&item.images.length>0)?item.images[0]:'';
      el.innerHTML=(thumb?'<img src="'+thumb+'" alt="'+esc(item.name)+'">':'<div class="img-placeholder">'+ICONS.car+'</div>')+
        '<div class="likes-item-name">'+esc(item.name)+'</div>';
      grid.appendChild(el);
    }});
  }}
  document.getElementById('likesScreen').classList.add('visible');
}}
function hideLikes() {{document.getElementById('likesScreen').classList.remove('visible');}}
function copyLikes() {{
  const names=likes.map(id=>{{const item=allItems.find(i=>i.id===id);return item?item.name:id;}});
  navigator.clipboard.writeText(names.join('\\n')).then(()=>{{
    const btn=document.querySelector('.btn-copy');
    btn.textContent='Copied!';setTimeout(()=>{{btn.textContent='Copy List';}},1500);
  }});
}}
function startOver() {{likes=[];seen=[];history=[];save();hideLikes();buildDeck();}}

function showModal(item) {{
  const modal=document.getElementById('modal');
  let h='<button class="modal-close" onclick="closeModal()">'+ICONS.x+' Close</button>';
  h+='<div class="card-images">';
  if(item.images&&item.images.length>0) {{
    item.images.forEach((src,idx)=>{{h+='<img src="'+src+'" alt="'+esc(item.name)+'"'+(idx===0?' class="visible"':'')+'>';}});
    if(item.images.length>1) {{
      h+='<div class="img-dots">';item.images.forEach((_,idx)=>{{h+='<span'+(idx===0?' class="active"':'')+'></span>';}});h+='</div>';
      h+='<div class="img-tap-zone left" onclick="modalImg(-1)"></div>';
      h+='<div class="img-tap-zone right" onclick="modalImg(1)"></div>';
    }}
  }} else h+='<div class="img-placeholder">'+ICONS.car+'</div>';
  h+='</div>';
  if(item.badge) h+='<div class="card-badge" style="position:relative;display:inline-flex;margin-bottom:6px;">'+getIcon('fuel')+' '+esc(item.badge)+'</div>';
  h+='<div class="card-name" style="padding-right:0">'+esc(item.name)+'</div>';
  h+='<div class="card-subtitle">'+esc(item.subtitle)+'</div>';
  if(item.stats&&item.stats.length>0) {{
    h+='<div class="stats-grid" style="margin-top:10px">';
    item.stats.forEach(s=>{{h+='<div class="stat">'+getIcon(s.icon)+'<div class="stat-text"><span class="stat-label">'+esc(s.label)+'</span><span class="stat-value">'+esc(s.value)+'</span>'+(s.note?'<span class="stat-note">'+esc(s.note)+'</span>':'')+'</div></div>';}});
    h+='</div>';
  }}
  if((item.pros&&item.pros.length)||(item.cons&&item.cons.length)) {{
    h+='<div class="pros-cons" style="margin-top:10px">';
    if(item.pros){{h+='<ul>';item.pros.forEach(p=>{{h+='<li class="pro">'+ICONS.check+' '+esc(p)+'</li>';}});h+='</ul>';}}
    if(item.cons){{h+='<ul>';item.cons.forEach(c=>{{h+='<li class="con">'+ICONS.x+' '+esc(c)+'</li>';}});h+='</ul>';}}
    h+='</div>';
  }}
  if(item.vibe) h+='<div class="card-vibe" style="margin-top:8px">'+esc(item.vibe)+'</div>';
  if(item.footnote) h+='<div class="card-footnote">'+esc(item.footnote)+'</div>';
  modal.innerHTML=h;modal._imgIndex=0;
  document.getElementById('modalOverlay').classList.add('visible');
}}
window.modalImg=function(dir){{
  const modal=document.getElementById('modal');
  const imgs=modal.querySelectorAll('.card-images img');
  const dots=modal.querySelectorAll('.img-dots span');
  if(imgs.length<2) return;
  let idx=(modal._imgIndex||0)+dir;
  if(idx<0)idx=0;if(idx>=imgs.length)idx=imgs.length-1;
  modal._imgIndex=idx;
  imgs.forEach((img,i)=>img.classList.toggle('visible',i===idx));
  dots.forEach((d,i)=>d.classList.toggle('active',i===idx));
}};
function closeModal(e) {{
  if(e&&e.target!==document.getElementById('modalOverlay')&&e.type==='click') return;
  document.getElementById('modalOverlay').classList.remove('visible');
}}

function init() {{
  setRegion(region);
  initBudget();
  save();
  buildDeck();
}}
init();

if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(()=>{{}});
</script>
</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")
