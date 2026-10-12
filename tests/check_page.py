"""Page checks (copied from the website repo, sunithi2000-lab/kutcheri): open the app page in a headless Chromium phone browser and use it like a visitor.

Needs: pip install playwright && playwright install --with-deps chromium
Usage: python3 tests/check_page.py [path/to/index.html]
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parent.parent
page_file = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else R / "index.html"
c = json.loads((R / "data/concerts.json").read_text())
o = json.loads((R / "data/organisations.json").read_text())
problems = []


def check(ok, msg):
    if not ok:
        problems.append(msg)


def no_overlap(pg, label):
    gap = pg.evaluate("""() => { let worst = 99;
      document.querySelectorAll('.kc').forEach(k => { const t = k.querySelector('.kt'), n = k.querySelector('.kb'); if (!t || !n) return;
        const right = Math.max(...[...t.children].map(e => { const r = document.createRange(); r.selectNodeContents(e); return r.getBoundingClientRect().right; }));
        worst = Math.min(worst, n.getBoundingClientRect().left - right); }); return worst; }""")
    check(gap >= 2, f"{label}: concert times overlap the artist names (gap {gap:.1f}px)")


with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True, color_scheme=scheme)
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file:") else r.abort())  # stay offline
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "net::ERR" not in m.text else None)
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(700)
        tag = f"[{scheme}]"

        cards = pg.locator(".kc").count()
        check(cards == len(c), f"{tag} list shows {cards} concerts, data has {len(c)}")
        check(f"{len(c)} of {len(c)}" in pg.locator("#count").inner_text(), f"{tag} counter text wrong: {pg.locator('#count').inner_text()!r}")
        check(pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), f"{tag} page scrolls sideways on a 360px phone")
        no_overlap(pg, tag)
        n_org_opts = pg.locator("#org option").count() - 1
        check(n_org_opts == len(o), f"{tag} sabha filter lists {n_org_opts} organisations, data has {len(o)}")
        check(pg.locator("#type option").count() > 1 and pg.locator("#area option").count() > 1, f"{tag} type/area filters are empty")

        # search
        artist = c[0]["main_artist"].split()[0]
        pg.fill("#q", artist)
        pg.wait_for_timeout(200)
        hits = pg.locator(".kc").count()
        check(0 < hits < len(c), f"{tag} searching '{artist}' gave {hits} results")
        pg.fill("#q", "")
        # date strip
        first_day = sorted({x["date"] for x in c})[0]
        pg.click(f'.dy[data-d="{first_day}"]')
        pg.wait_for_timeout(200)
        want = sum(1 for x in c if x["date"] == first_day)
        check(pg.locator(".kc").count() == want, f"{tag} picking {first_day} shows {pg.locator('.kc').count()} concerts, expected {want}")
        pg.click(f'.dy[data-d="{first_day}"]')
        # calendar sheet opens and closes
        pg.click("#openf")
        check(pg.locator("#sheet").is_visible(), f"{tag} Calendar sheet does not open")
        pg.click("#done")
        # star -> My plan
        pg.locator(".star").first.click()
        pg.click('.tab[data-v="fav"]')
        pg.wait_for_timeout(200)
        check(pg.locator("#fav .kc").count() == 1, f"{tag} My plan shows {pg.locator('#fav .kc').count()} concerts after starring one")
        # Sabhas tab
        pg.click('.tab[data-v="orgs"]')
        pg.wait_for_timeout(200)
        n_orgs = pg.locator("#orgs .org").count()
        check(n_orgs == len(o), f"{tag} Sabhas tab lists {n_orgs}, data has {len(o)}")
        check("Organiser not stated" not in pg.locator("#orgs").inner_text(), f'{tag} Sabhas tab shows "Organiser not stated"')
        pg.click('.tab[data-v="list"]')
        # pinned date strip: after scrolling, the strip is still on screen and the cards are below it
        pg.mouse.wheel(0, 1500)
        pg.wait_for_timeout(300)
        strip = pg.locator("#strip").bounding_box()
        check(strip is not None and strip["y"] >= -1 and strip["y"] < 200, f"{tag} date strip is not pinned at the top when scrolling ({strip})")
        check(not errors, f"{tag} JavaScript errors: {errors[:3]}")
        ctx.close()

    # large phone text: times must still clear the names
    ctx = b.new_context(viewport={"width": 360, "height": 740})
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file:") else r.abort())
    pg = ctx.new_page()
    pg.goto(page_file.as_uri())
    pg.wait_for_timeout(400)
    # enlarge the text after the page has loaded (like a font arriving late or the phone's text size changing)
    pg.add_style_tag(content=".kt b{font-size:21px!important}.kt small{font-size:17px!important}")
    pg.wait_for_timeout(400)
    no_overlap(pg, "[large text]")
    # error reporting is wired up
    pg.evaluate("setTimeout(() => { throw new Error('health-check test error'); })")
    pg.wait_for_timeout(200)
    check(any("health-check test error" in e for e in pg.evaluate("window.__errs || []")), "error reporting did not capture a test error")
    b.close()

if problems:
    print(f"PAGE CHECK FAILED — {len(problems)} problem(s):")
    for x in problems:
        print(" -", x)
    sys.exit(1)
print(f"page OK: {len(c)} concerts render; search, dates, calendar, My plan, Sabhas, pinned strip, light/dark, large text, error capture")
