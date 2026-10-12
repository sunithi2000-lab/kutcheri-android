"""Build the app's web page (www/) from the website's page template and data.

Input:  web/list_template.html  - copied unchanged from the website repo (sunithi2000-lab/kutcheri)
        web/icon.svg
        data/concerts.json, data/organisations.json - the offline copy shipped inside the app
Output: www/index.html, www/icon.svg

App-only changes are applied here, so the website template can be re-copied as-is:
  * live data: on start the app downloads the latest list from the website, keeps it for
    offline use, and falls back to the copy shipped inside the app;
  * web links (Google Maps, sabha and artist websites) open in the phone's browser / Maps app;
  * Android safe-area insets (status bar and gesture bar) come from Capacitor's CSS variables.
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
missing = {x["organisation"] for x in c} - {x["name"] for x in o}
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
const LIVE = (() => {{ try {{ const v = JSON.parse(localStorage.getItem("mk-live"));
  return v && v.at > APP_BUILD && Array.isArray(v.c) && v.c.length && Array.isArray(v.o) ? v : null; }} catch (e) {{ return null; }} }})();
const CONCERTS = LIVE ? LIVE.c : BUNDLED_C;
const ORGS = LIVE ? LIVE.o : BUNDLED_O;
const DATA_SIG = JSON.stringify(CONCERTS) + JSON.stringify(ORGS);""")

LIVE_JS = r"""
// ---- app: fetch the latest list from the website; keep it for offline use
(() => {
  let touched = false;
  ["pointerdown", "keydown"].forEach(ev => addEventListener(ev, () => { touched = true; }, { once: true, capture: true }));
  const SOURCES = ["https://kutcheri-dec.netlify.app/", "https://raw.githubusercontent.com/sunithi2000-lab/kutcheri/main/"];
  const get = url => fetch(url + "?t=" + Date.now(), { cache: "no-store" }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const banner = () => {
    if (document.getElementById("app-upd")) return;
    const b = document.createElement("button");
    b.id = "app-upd"; b.type = "button"; b.textContent = "Updated concert list available · Tap to refresh";
    b.style.cssText = "position:fixed;left:12px;right:12px;bottom:calc(76px + var(--safe-area-inset-bottom, 0px));z-index:60;" +
      "padding:12px 14px;border:0;border-radius:12px;background:#0E6A57;color:#fff;font:600 14px/1.3 system-ui,sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.25)";
    b.onclick = () => location.reload();
    document.body.appendChild(b);
  };
  (async () => {
    for (const base of SOURCES) {
      try {
        const [c, o] = await Promise.all([get(base + "data/concerts.json"), get(base + "data/organisations.json")]);
        if (!Array.isArray(c) || !c.length || !Array.isArray(o) || !o.length) throw new Error("bad data");
        const at = new Date().toISOString();
        if (JSON.stringify(c) + JSON.stringify(o) === DATA_SIG) {
          if (LIVE) store.set("mk-live", { at, c, o });
          return;
        }
        store.set("mk-live", { at, c, o });
        touched ? banner() : location.reload();
        return;
      } catch (e) { /* offline or source down: try the next one, else keep the saved copy */ }
    }
  })();
})();

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

# 3. embed the offline copy of the data
j = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
t = t.replace("/*__CONCERTS__*/[]", j(c)).replace("/*__ORGS__*/[]", j(o))

head, body = t.split("</style>", 1)
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0E6A57">
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
(www / "icon.svg").write_text((R / "web/icon.svg").read_text())
(R / "tools/_check.js").write_text(re.search(r"<script>(.*)</script>", doc, re.S).group(1))
print(f"www/index.html: {len(c)} concerts, {len(o)} organisations, build {build}")
