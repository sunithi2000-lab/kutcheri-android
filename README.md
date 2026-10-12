# Marghazhi Kutcheri Planner — Android app

Android version of the Chennai Margazhi 2026–27 Carnatic concert planner (website: https://kutcheri-dec.netlify.app, code: [sunithi2000-lab/kutcheri](https://github.com/sunithi2000-lab/kutcheri)). The website is not changed by anything in this repo.

Built with [Capacitor 8](https://capacitorjs.com): the app shows the same planner page, stored inside the app so it works offline.

## How the concert list stays current
- Each app build ships an offline copy of `data/concerts.json` and `data/organisations.json` (refreshed from the website at build time).
- When the phone is online, the app downloads the latest list from the website (fallback: GitHub) and keeps it for offline use. If the list changed before the user has touched the screen, the app reloads quietly; otherwise it shows a "Tap to refresh" bar. So the website's daily update reaches the app without a new release.
- Favourites ("My plan") and filters are stored on the phone only.

## Building
GitHub Actions builds everything (`.github/workflows/android.yml`) on every push to `main`, or on demand from **Actions → Build Android app → Run workflow**:
- `kutcheri-planner-1.0.N.aab` — signed bundle to upload to Google Play
- `kutcheri-planner-1.0.N.apk` — signed APK that installs directly on a phone for testing
Both appear under **Releases** and as a downloadable artifact of the run. `N` (the version code) is the run number, so every build can be uploaded.

Signing uses the upload key in `signing/upload-key.p12` (password-protected PKCS12, alias `upload`) and the repository secret `KEYSTORE_PASSWORD`. Without that secret the workflow builds only an unsigned-for-Play debug test APK.

## Files
| Path | Purpose |
|---|---|
| `web/list_template.html`, `web/icon.svg` | Copied unchanged from the website repo |
| `tools/build_www.py` | Makes `www/index.html`: embeds the data and adds the app-only parts (live update, links open outside the app, Android safe areas) |
| `data/` | Offline copy of the concert list |
| `capacitor.config.json` | App id `io.github.sunithi2000lab.kutcheri`, name "Kutcheri Planner" |
| `resources/` | Icon and splash source images (turned into Android sizes by `@capacitor/assets`) |
| `scripts/patch_android.py` | Sets version and signing in the generated `android/` project |
| `store/` | Google Play listing graphics and text |
| `PRIVACY.md` | Privacy policy (link this in Play Console) |

## Updating the app's page from the website
Copy `list_template.html` and `icon.svg` from the website repo into `web/`, then push. If the build fails at `tools/build_www.py`, the template changed in a place the app patches — update the matching `sub(...)` line.
