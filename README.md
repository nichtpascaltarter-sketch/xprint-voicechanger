# X-PRINT // VOICE CHANGER

**Echtzeit-Stimmverzerrer für Windows** – Discord-ready – X-Print Industrial Design.
**Optimiert für Python 3.15.0a8** mit Fallbacks für 3.11 / 3.12 / 3.13.

```
╔══════════════════════════════════════════════════════════╗
║  Mikrofon  →  X-Print Engine  →  VB-CABLE  →  Discord    ║
╚══════════════════════════════════════════════════════════╝
```

---

## ⚡ FEATURES

- **ERWACHSEN-Modus** – Pitch −12 Halbtöne, Formant-Absenkung, tiefe markante Stimme
- **BABY-Modus** – Pitch +7 Halbtöne, Formant-Anhebung, dezentes Doubling (**kein Chipmunk-Effekt**)
- **BYPASS-Toggle** – Originalstimme unverändert durchleiten
- **Live-Umschaltung** ohne Dropouts
- **VB-CABLE-Autodetektion** – Gerät wird erkannt, Download-Link bei Fehlen
- **Animierte Level-Meter** mit dB-Anzeige, Peak-Hold und −6/−12 dB-Markierungen
- **Zielatenz < 50 ms** bei Buffer 256 Samples @ 48 kHz
- **Hotkeys** – F1 Bypass, F2 Erwachsen, F3 Baby
- **Python 3.15-Alpha-aware** – defensive Imports + Pre-Release-Wheels

---

## 🧪 PYTHON 3.15-ALPHA – WICHTIGE HINWEISE

Python 3.15.0a8 ist eine **Alpha-Version**. Drittanbieter-Pakete liefern in dieser Phase nicht immer fertige Wheels. Das Projekt ist trotzdem darauf ausgelegt zu funktionieren – es braucht nur den richtigen Install-Pfad.

### Zwei mögliche Szenarien

**Szenario A — pip findet alle Wheels** *(Glücksfall)*
```powershell
py -3.15 -m venv venv
.\venv\Scripts\Activate.ps1
pip install --pre -r requirements.txt
python main.py
```

**Szenario B — pedalboard / numpy haben kein 3.15-Wheel** *(häufiger in Alphas)*
Dann muss aus dem Sourcecode kompiliert werden – dafür brauchst du:

1. **Visual Studio Build Tools 2022** mit Workload *„Desktop development with C++"*
   → https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Danach:
   ```powershell
   pip install --pre --no-binary=:all: numpy
   pip install --pre --no-binary=:all: pedalboard
   ```
   ⚠️ Numpy aus Source dauert **5–15 Minuten** und braucht ~2 GB RAM beim Build.

**Szenario C — etwas funktioniert in 3.15 gar nicht** *(z. B. PyInstaller-Hooks)*
Nur für den **Build** auf Python 3.13 zurückwechseln (Code läuft, nur die `.exe`-Erstellung ist betroffen):
```powershell
py -3.13 -m venv venv-build
.\venv-build\Scripts\Activate.ps1
pip install --pre -r requirements.txt pyinstaller
.\build.bat
```
Die fertige `.exe` enthält ein gebündeltes Python und läuft unabhängig von der Systeminstallation.

---

## 📦 INSTALLATION (Endbenutzer)

### Schritt 1 — VB-CABLE installieren (**Pflicht** für Discord)

1. Download: **https://vb-audio.com/Cable/**
2. ZIP entpacken → `VBCABLE_Setup_x64.exe` **als Administrator** ausführen
3. **Windows neu starten** (wichtig, sonst taucht das Gerät nicht auf)

### Schritt 2 — X-Print Voice Changer installieren

- Installer: `XPrint-VoiceChanger-Setup-1.0.0.exe`
- Fügt Startmenü-Eintrag + optional Desktop-Verknüpfung hinzu
- Saubere Deinstallation über *Apps & Features* in Windows

---

## 🎙️ BENUTZUNG MIT DISCORD

### 1) X-Print Voice Changer starten

| Feld    | Einstellung                                            |
|---------|--------------------------------------------------------|
| INPUT   | Dein echtes Mikrofon (z. B. *Microphone [WASAPI]*)     |
| OUTPUT  | **CABLE Input (VB-Audio Virtual Cable) [WASAPI]**      |
| Modus   | ERWACHSEN / BABY / BYPASS nach Geschmack               |
| Buffer  | 256 (Default), bei Knacken → 512 / 1024                |

### 2) Discord konfigurieren

1. Discord → **Einstellungen** → **Sprache & Video**
2. **Eingabegerät**: `CABLE Output (VB-Audio Virtual Cable)`
3. **Ausgabegerät**: deine normalen Kopfhörer/Lautsprecher
4. **Empfindlichkeit**: manuell, ca. −40 dB
5. **Automatische Verstärkungsregelung**: ⛔ AUS
6. **Echo-/Rauschunterdrückung**: ⛔ AUS (optional testen)
7. **Lautstärke-Normalisierung**: ⛔ AUS

---

## ⏱️ LATENZ & PERFORMANCE

| Buffer (Samples) | Ungefähre Gesamt-Latenz |
|-----------------:|-------------------------|
| 128              | ~15 – 25 ms             |
| **256** (Default)| **~25 – 40 ms**         |
| 512              | ~40 – 60 ms             |
| 1024             | ~60 – 100 ms            |

**Bei Audio-Knistern / Dropouts** → Buffer eine Stufe erhöhen.

**Getestet auf**: Intel i9-14900K · 128 GB RAM · RTX 5090 · Windows 11 Pro
**Minimum**: Quad-Core CPU · 4 GB RAM · Windows 10 64-bit

---

## 🔧 BUILD FROM SOURCE

```powershell
# Voraussetzung: Python 3.15.0a8 (oder 3.11+) im PATH oder via py-Launcher
git clone https://github.com/nichtpascaltarter-sketch/xprint-voicechanger.git
cd xprint-voicechanger

# Development-Run (legt automatisch venv an)
py -3.15 -m venv venv
.\venv\Scripts\Activate.ps1
pip install --pre -r requirements.txt
python main.py

# Single-File .exe bauen
.\build.bat
# -> dist\XPrint-VoiceChanger.exe
```

### Installer kompilieren

1. [Inno Setup 6](https://jrsoftware.org/isdl.php) installieren
2. `installer.iss` öffnen → **Build** → **Compile** (`Strg+F9`)
3. Output: `installer_output\XPrint-VoiceChanger-Setup-1.0.0.exe`

---

## 📂 PROJEKTSTRUKTUR

```
xprint-voice/
├── main.py              # GUI + App-Lifecycle (customtkinter)
├── audio_engine.py      # sounddevice-Callback + pedalboard-Ketten
├── device_manager.py    # Device-Listing + VB-CABLE-Erkennung
├── requirements.txt     # Python-Dependencies (unpinned für 3.15)
├── build.bat            # PyInstaller-Build-Script (3.15-aware)
├── installer.iss        # Inno-Setup-Script
├── README.md            # Du bist hier
└── dist/                # (nach build.bat)
    └── XPrint-VoiceChanger.exe
```

---

## 🩺 TROUBLESHOOTING

| Problem                                  | Lösung                                                                   |
|------------------------------------------|--------------------------------------------------------------------------|
| `No matching distribution found for pedalboard` | Python 3.15-Wheels noch nicht da → siehe Szenario B oben            |
| `Microsoft Visual C++ 14.0 or greater required` | VS Build Tools 2022 mit C++-Workload installieren                   |
| `ModuleNotFoundError: sounddevice`       | venv nicht aktiviert (`Activate.ps1`) oder falscher Python-Interpreter   |
| *"CABLE Output" fehlt in Discord*        | Windows nach VB-CABLE-Install **neu starten**                            |
| *Stimme knackst/stottert*                | Buffer auf 512 oder 1024 erhöhen                                         |
| *Kein Input-Pegel sichtbar*              | Windows → *Datenschutz* → *Mikrofon* für Apps freigeben                  |
| *Latenz zu hoch*                         | Beide Dropdowns auf **WASAPI** setzen, Buffer = 256                      |
| *PyInstaller-Build crasht*               | Build mit Python 3.13 statt 3.15 (siehe Szenario C oben)                 |
| *Installer verweigert Start*             | Als Administrator ausführen, SmartScreen → *Trotzdem ausführen*          |
| `cannot be loaded because running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`           |

---

## 🧪 PYTHON 3.15 – DEBUGGING

Im Hotkey-Bereich oben rechts in der App erscheint bei Pre-Release-Python automatisch ein Hinweis (`⚠ Python 3.15 alpha8 -- experimentell`). So siehst du sofort, gegen welche Version die `.exe` gelinkt wurde.

Bei Crashs lieferst du diese Infos:

```powershell
python --version
python -c "import sounddevice, numpy, pedalboard; print(sounddevice.__version__, numpy.__version__, pedalboard.__version__)"
python -c "import sounddevice as sd; [print(d) for d in sd.query_devices()]"
```

---

## 🎨 EFFEKT-DETAILS (technisch)

**ERWACHSEN** (Pedalboard-Chain):
```
Highpass @ 70 Hz  →  PitchShift −12 st  →  LowShelf +3.5 dB @ 220 Hz
→  HighShelf −2 dB @ 4.5 kHz  →  Compressor 3:1  →  Gain +2.5  →  Limiter −1 dB
```

**BABY** (Pedalboard-Chain):
```
Highpass @ 120 Hz  →  PitchShift +7 st  →  HighShelf +4 dB @ 3.2 kHz
→  LowShelf −2.5 dB @ 180 Hz  →  Chorus (Doubling)  →  Compressor 2.5:1
→  Gain +1  →  Limiter −1 dB
```

Der Limiter am Ende verhindert Clipping auch bei lautem Input — wichtig für Discord.

---

## 📝 LIZENZ / CREDITS

© 2026 **X-Print**, Thun, Schweiz
Powered by: Python 3.15 · customtkinter · sounddevice (PortAudio) · pedalboard (Spotify)

*VB-CABLE ist ein Produkt von VB-Audio Software, Donationware, **nicht** von X-Print.*
