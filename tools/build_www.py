"""Build the app's web page (www/) from the website's page template and data.

Input:  web/list_template.html  - copied unchanged from the website repo (sunithi2000-lab/kutcheri)
        web/icon.svg
        data/concerts.json, data/organisations.json - the offline copy shipped inside the app
Output: www/index.html, www/icon.svg

App-only changes are applied here, so the website template can be re-copied as-is:
  * live data: on start the app downloads the latest list from the website, keeps it for
    offline use, and falls back to the copy shipped inside the app;
  * web links (Google Maps, sabha and artist websites) open in the phone's browser / Maps app;
  * (status/navigation bars are handled natively in MainActivity, see scripts/patch_android.py)
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent.parent
t = (R / "web/list_template.html").read_text()
c = json.loads((R / "data/concerts.json").read_text())
o = json.loads((R / "data/organisations.json").read_text())
assert c and o, "empty data"
missing = {x["organisation"] for x in c} - {x["name"] for x in o} - {"Organiser not stated"}  # a label, not an organisation
assert not missing, f"organisations missing: {missing}"


def sub(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f"expected {count}x {old[:60]!r}, found {n} - website template changed; update tools/build_www.py"
    t = t.replace(old, new)


# 1. live data with offline copy
build = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
sub("const CONCERTS = /*__CONCERTS__*/[];\nconst ORGS = /*__ORGS__*/[];", f"""const APP_BUILD = "{build}";
const BUNDLED_C = /*__CONCERTS__*/[], BUNDLED_O = /*__ORGS__*/[];
const LIVE = null; // live updates off: ignore any saved downloaded list
const CONCERTS = LIVE ? LIVE.c : BUNDLED_C;
const ORGS = LIVE ? LIVE.o : BUNDLED_O;
const DATA_SIG = JSON.stringify(CONCERTS) + JSON.stringify(ORGS);""")

LIVE_JS = r"""
// ---- app: live updates switched off 26 Nov 2026 (owner's request); the app shows only the list bundled at build time

// ---- app: open web links (Maps, sabha and artist sites) outside the app
document.addEventListener("click", e => {
  const a = e.target.closest('a[href^="http"]');
  if (!a) return;
  e.preventDefault();
  location.href = a.href;
}, true);
</script>"""
assert t.rstrip().endswith("</script>"), "template no longer ends with the page script"
t = t.rstrip()[: -len("</script>")] + LIVE_JS.lstrip("\n") + "\n"

# 2. safe areas from Capacitor's SystemBars plugin
for side in ("top", "bottom"):
    t = t.replace(f"env(safe-area-inset-{side}, 0px)", f"var(--safe-area-inset-{side}, env(safe-area-inset-{side}, 0px))")

# (pinned date strip and the measured time column now live in the shared website template)

# 3. embed the offline copy of the data
j = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
t = t.replace("/*__CONCERTS__*/[]", j(c)).replace("/*__ORGS__*/[]", j(o))

head, body = t.split("</style>", 1)
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#F39C1E">
<meta name="format-detection" content="telephone=no">
<link rel="icon" href="icon.svg" type="image/svg+xml">
{head}</style>
</head>
<body>
{body}
</body>
</html>
"""
www = R / "www"
www.mkdir(exist_ok=True)
(www / "index.html").write_text(doc)
(www / "icon.svg").write_text((R / "resources/app-icon.svg").read_text())
(R / "tools/_check.js").write_text(re.search(r"<script>(.*)</script>", doc, re.S).group(1))
print(f"www/index.html: {len(c)} concerts, {len(o)} organisations, build {build}")
