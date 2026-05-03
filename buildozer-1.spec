[app]

# ── መሰረታዊ መረጃ / Basic Info ──────────────────────────────────────────────────
title           = የንግድ ስራ ረዳት
package.name    = yenigdapp
package.domain  = org.yenigdapp

source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,txt,md

# ── ዋና ፋይል / Entry point ────────────────────────────────────────────────────
# main file must be named main.py for buildozer
# Rename business_app.py → main.py in your repo
source.main      = main.py

version          = 1.0.0

# ── Requirements ─────────────────────────────────────────────────────────────
# sqlite3 is built-in to Python — no extra package needed
requirements = python3,kivy==2.3.0,pillow

# ── Font file: include Nyala.ttf ─────────────────────────────────────────────
# Place Nyala.ttf in your repo root alongside main.py
source.include_patterns = Nyala.ttf

# ── Icons & Splash ───────────────────────────────────────────────────────────
# Uncomment and add your own files when ready:
# icon.filename      = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# ── Orientation ──────────────────────────────────────────────────────────────
orientation = portrait

# ── Android ──────────────────────────────────────────────────────────────────
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, INTERNET

# API 21 = Android 5.0 (ሁሉም አዲስ ስልኮች ይሰራሉ)
android.minapi   = 21
android.api      = 33
android.ndk      = 25b
android.archs    = arm64-v8a, armeabi-v7a

# Enable backup (optional)
android.allow_backup = True

# ── iOS (ለወደፊት / future use) ────────────────────────────────────────────────
# ios.kivy_ios_url  = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master

# ── Log / Debug ──────────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
