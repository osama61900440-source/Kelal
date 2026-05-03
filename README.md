# 🛒 የንግድ ስራ ረዳት — Business Assistant App

> Python + Kivy + SQLite — Android APK via Buildozer

---

## 📁 የ Repo አቀማመጥ / Repo Structure

```
├── main.py            ← business_app.py ስሙን ቀይሩ
├── buildozer.spec
├── Nyala.ttf          ← አማርኛ ፊደል (optional)
└── README.md
```

> **ⓘ ማስታወሻ:** `business_app.py` → `main.py` ብለው ስሙን ይቀይሩ!  
> Buildozer always looks for `main.py`.

---

## ✨ ባህርያት / Features

| ደረጃ | Feature |
|------|---------|
| 1️⃣ | እቃ ምዝገባ — SQLite item registry with Spinner |
| 2️⃣ | የጭነት ወጪ ማከፋፈያ — Landed cost distributor |
| 3️⃣ | ትርፍ ትንበያ — Profit & daily sales forecast |
| 4️⃣ | 70/20/5/5 በጀት ክፍፍል — Budget planner |
| 5️⃣ | ታሪክ ማህደር — Full SQLite history viewer |

---

## 🖥️ Desktop ላይ ለማሂድ / Run on Desktop

```bash
pip install kivy
python main.py
```

---

## 📱 Android APK ለመስራት / Build Android APK

### 1. Ubuntu / WSL2 / GitHub Actions ይጠቀሙ

```bash
# Install buildozer
pip install buildozer

# Install system dependencies (Ubuntu)
sudo apt update
sudo apt install -y \
    git zip unzip openjdk-17-jdk \
    python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev

# Build debug APK
buildozer android debug

# APK will be in:  .buildozer/android/platform/build/dists/yenigdapp/
# or:              bin/yenigdapp-1.0.0-arm64-v8a-debug.apk
```

### 2. ለስልክ ላይ ለመጫን / Install on phone

```bash
# USB debugging on → then:
buildozer android deploy run
```

---

## 🤖 GitHub Actions (Cloud Build — ነፃ!)

`.github/workflows/build.yml` ፋይል ይፍጠሩ:

```yaml
name: Build APK

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          sudo apt update
          sudo apt install -y git zip unzip openjdk-17-jdk \
            python3-pip autoconf libtool pkg-config \
            zlib1g-dev libncurses5-dev libncursesw5-dev \
            libtinfo5 cmake libffi-dev libssl-dev
          pip install buildozer cython

      - name: Build APK
        run: buildozer android debug

      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: business-app-apk
          path: bin/*.apk
```

> APK ሲሰራ GitHub → Actions → Artifacts ውስጥ ያውርዱ።

---

## 🔤 Amharic Font

- Windows: `C:\Windows\Fonts\Nyala.ttf` → copy to repo root
- App falls back to default font if Nyala.ttf is missing

---

## 📋 Requirements

```
kivy==2.3.0
python3
pillow
sqlite3  ← built-in, no install needed
```

---

## 📄 License

MIT
