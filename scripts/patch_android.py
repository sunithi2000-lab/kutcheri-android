"""Adjust the generated android/ project (run after `npx cap add android`).

* versionCode / versionName from env VERSION_CODE (the GitHub Actions run number)
* release signing from env KEYSTORE_FILE, KEYSTORE_PASSWORD, KEY_ALIAS, KEY_PASSWORD
* keep the WebView from reloading when the screen size / density changes
Fails loudly if Capacitor's template changes shape, so nothing is silently skipped.
"""
import os
import re
from pathlib import Path

A = Path(__file__).resolve().parent.parent / "android"
g = A / "app/build.gradle"
s = g.read_text()

code = int(os.environ.get("VERSION_CODE", "1"))
s, n1 = re.subn(r"versionCode\s+\d+", f"versionCode {code}", s)
s, n2 = re.subn(r'versionName\s+"[^"]*"', f'versionName "1.0.{code}"', s)
assert n1 == 1 and n2 == 1, "versionCode/versionName not found in app/build.gradle"

signing = """
    signingConfigs {
        release {
            if (System.getenv("KEYSTORE_FILE")) {
                storeFile file(System.getenv("KEYSTORE_FILE"))
                storePassword System.getenv("KEYSTORE_PASSWORD")
                keyAlias System.getenv("KEY_ALIAS")
                keyPassword System.getenv("KEY_PASSWORD")
            }
        }
    }
    buildTypes {"""
s, n3 = re.subn(r"\n    buildTypes \{", signing, s, count=1)
s, n4 = re.subn(r"(buildTypes \{\s*\n\s*release \{)", r"\1\n            signingConfig signingConfigs.release", s, count=1)
assert n3 == 1 and n4 == 1, "buildTypes/release block not found in app/build.gradle"
g.write_text(s)

m = A / "app/src/main/AndroidManifest.xml"
x = m.read_text()
x2, n5 = re.subn(r'android:configChanges="([^"]*)"', lambda mo: mo.group(0) if "density" in mo.group(1) else f'android:configChanges="{mo.group(1)}|density"', x, count=1)
assert n5 == 1, "configChanges not found in AndroidManifest.xml"
m.write_text(x2)

v = (A / "variables.gradle").read_text()
sdk = dict(re.findall(r"(\w+SdkVersion)\s*=\s*(\d+)", v))
print("android patched: versionCode", code, "| sdk", sdk)
assert int(sdk.get("targetSdkVersion", 0)) >= 35, "Google Play needs targetSdk 35 or higher"
