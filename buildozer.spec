[app]

title           = የንግድ ስራ ረዳት
package.name    = kelalapp
package.domain  = org.kelalapp

source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,md
source.include_patterns = Nyala.ttf

version = 1.0.1

# FIX-5: removed python3 and sqlite3 — both are built-in, adding them breaks build
requirements = kivy==2.3.0,pillow

orientation  = portrait
fullscreen   = 0

android.permissions     = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.minapi          = 21
android.api             = 33
android.ndk             = 25b
android.archs           = arm64-v8a,armeabi-v7a
android.allow_backup    = True
android.logcat_filters  = *:S python:D

[buildozer]
log_level    = 2
warn_on_root = 1
