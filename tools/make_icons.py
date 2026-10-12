"""Draw the app icon, splash and Play Store graphics: saffron background, maroon beamed notes.
Run: python3 tools/make_icons.py (needs Playwright with Chromium)."""
from playwright.sync_api import sync_playwright
from pathlib import Path
R = str(Path(__file__).resolve().parent.parent)  # repo root
SAF, INK = "#F39C1E", "#5A1212"
# beamed pair of eighth notes, drawn in a 512 box; bbox ~ x 104..420, y 92..420, centre (262, 256)
NOTES = f'''<g fill="{INK}">
<ellipse cx="168" cy="368" rx="64" ry="46" transform="rotate(-22 168 368)"/>
<ellipse cx="356" cy="328" rx="64" ry="46" transform="rotate(-22 356 328)"/>
<rect x="208" y="140" width="24" height="222" rx="4"/>
<rect x="396" y="100" width="24" height="222" rx="4"/>
<polygon points="208,132 420,88 420,146 208,190"/>
</g>'''
def notes(cx, cy, h):
    k = h / 330
    return f'<g transform="translate({cx},{cy}) scale({k}) translate(-262,-256)">{NOTES}</g>'
jobs = {
  "resources/icon-only.png": (1024, 1024, f'<rect width="1024" height="1024" fill="{SAF}"/>' + notes(512, 512, 600)),
  "resources/icon-foreground.png": (1024, 1024, notes(512, 512, 500)),
  "resources/icon-background.png": (1024, 1024, f'<rect width="1024" height="1024" fill="{SAF}"/>'),
  "resources/splash.png": (2732, 2732, f'<rect width="2732" height="2732" fill="{SAF}"/>' + notes(1366, 1366, 460)),
  "resources/splash-dark.png": (2732, 2732, f'<rect width="2732" height="2732" fill="{SAF}"/>' + notes(1366, 1366, 460)),
  "store/icon-512.png": (512, 512, f'<rect width="512" height="512" fill="{SAF}"/>' + notes(256, 256, 300)),
  "store/feature-graphic.png": (1024, 500, f'''<rect width="1024" height="500" fill="{SAF}"/>
    {notes(190, 250, 260)}
    <text x="340" y="215" font-family="DejaVu Sans, sans-serif" font-weight="700" font-size="58" fill="{INK}">Marghazhi</text>
    <text x="340" y="285" font-family="DejaVu Sans, sans-serif" font-weight="700" font-size="58" fill="{INK}">Kutcheri Planner</text>
    <text x="342" y="345" font-family="DejaVu Sans, sans-serif" font-size="28" fill="#FFF7EA">Chennai December season · Carnatic concerts</text>'''),
}
svg_icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="112" fill="{SAF}"/>{notes(256, 256, 300)}</svg>\n'
open(f"{R}/resources/app-icon.svg", "w").write(svg_icon)
with sync_playwright() as p:
    b = p.chromium.launch()
    for path, (w, h, inner) in jobs.items():
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.set_content(f'<html><body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block">{inner}</svg></body></html>')
        pg.screenshot(path=f"{R}/{path}", omit_background="foreground" in path); pg.close()
    b.close()
