[app]

# ── መሰረታዊ መረጃ ──────────────────────────────────────────────────────────────
title          = የንግድ ስራ ረዳት
package.name   = kelalapp
package.domain = org.kelalapp

# ── ምንጭ ─────────────────────────────────────────────────────────────────────
source.dir             = .
source.include_exts    = py,png,jpg,kv,atlas,ttf,txt,md
# Nyala.ttf — አማርኛ ፊደላት ለ Kivy Label font_name="Nyala" ሲጠቀሙ
source.include_patterns = Nyala.ttf

# ── ቅጂ ──────────────────────────────────────────────────────────────────────
version = 1.0.1

# ── Requirements ─────────────────────────────────────────────────────────────
# python3  → ግዴታ ነው፤ buildozer Android ላይ Python runtime ሲጭን ይፈልጋል
# sqlite3  → በ python3 ውስጥ አብሮ ስለሚመጣ ዝርዝር ውስጥ አያስፈልግም
# pillow   → image support ለ Kivy
requirements = python3,kivy==2.3.0,pillow

# ── ገጽታ ─────────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen  = 0

# ── Android ──────────────────────────────────────────────────────────────────
# API 33 (Android 13) ላይ READ/WRITE ብቻ አይበቃም — MANAGE_EXTERNAL_STORAGE ይጨምሩ
# INTERNET — network ባይጠቀሙም buildozer packaging ሲሰራ ያስፈልጋል
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# Target & min API
android.api    = 33
android.minapi = 21
android.ndk    = 25b

# arm64-v8a  → አዳዲስ ስልኮች (64-bit)
# armeabi-v7a → አሮጌ ስልኮች (32-bit)
android.archs = arm64-v8a,armeabi-v7a

android.allow_backup   = True
android.logcat_filters = *:S python:D

# ── UTF-8 encoding — .py ፋይሎች UTF-8 መሆናቸው ይጠበቃል ──────────────────────────
# (Python 3 default ነው፤ ፋይሉን ሲቀምጡ "Save as UTF-8" ያድርጉ)

[buildozer]
log_level    = 2
warn_on_root = 1
