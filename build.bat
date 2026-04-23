@echo off
REM ============================================================================
REM  X-Print Voice Changer - Build Script  (Python 3.15.0a8 / Alpha)
REM ----------------------------------------------------------------------------
REM  Ausführung in PowerShell:   .\build.bat
REM  Ausführung in CMD:          build.bat
REM ============================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ============================================================
echo   X-PRINT // VOICE CHANGER  --  BUILD  (Python 3.15-Alpha)
echo  ============================================================
echo.

REM --- Python 3.15 finden -----------------------------------------------------
REM  Reihenfolge: py-Launcher mit -3.15  >  python im PATH
set PY_CMD=
where py >nul 2>&1
if not errorlevel 1 (
    py -3.15 -c "import sys; assert sys.version_info[:2]==(3,15)" >nul 2>&1
    if not errorlevel 1 (
        set PY_CMD=py -3.15
        echo [OK]  Python 3.15 via py-Launcher gefunden.
    )
)

if "!PY_CMD!"=="" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [FEHLER] Weder 'py -3.15' noch 'python' im PATH gefunden.
        echo          Installiere Python 3.15.0a8 von https://www.python.org/downloads/
        pause
        exit /b 1
    )
    python -c "import sys; assert sys.version_info[:2]==(3,15)" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] python im PATH ist NICHT 3.15. Build geht trotzdem weiter,
        echo        aber die .exe wird gegen die falsche Python-Version gebaut.
        echo        Drücke Strg+C zum Abbrechen oder warte 5 Sekunden...
        timeout /t 5 >nul
    )
    set PY_CMD=python
)

echo [INFO] Verwende: !PY_CMD!
!PY_CMD! --version
echo.

REM --- Venv anlegen ----------------------------------------------------------
if not exist "venv" (
    echo [1/5] Erstelle virtuelle Umgebung mit !PY_CMD!...
    !PY_CMD! -m venv venv
    if errorlevel 1 (
        echo [FEHLER] venv konnte nicht erstellt werden.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

REM --- Pip aktualisieren -----------------------------------------------------
echo [2/5] Aktualisiere pip / setuptools / wheel...
python -m pip install --pre --upgrade pip setuptools wheel >nul

REM --- Dependencies (mit --pre für Alpha-Wheels) -----------------------------
echo [3/5] Installiere Dependencies (Pre-Releases erlaubt)...
python -m pip install --pre -r requirements.txt
if errorlevel 1 (
    echo.
    echo [WARN]  Standard-Install fehlgeschlagen.
    echo         Versuche Fallback: einzelne Pakete, Source-Build erlaubt.
    echo.
    python -m pip install --pre customtkinter sounddevice numpy
    if errorlevel 1 (
        echo [FEHLER] Auch Fallback fehlgeschlagen. Siehe README "Alpha-Build".
        pause
        exit /b 1
    )
    REM pedalboard separat - braucht oft Build-Tools
    python -m pip install --pre pedalboard
    if errorlevel 1 (
        echo [FEHLER] pedalboard konnte nicht installiert werden.
        echo          Installiere "Visual Studio Build Tools 2022" mit C++ Workload,
        echo          dann erneut versuchen. Details in README.
        pause
        exit /b 1
    )
)

echo [3b/5] Installiere PyInstaller...
python -m pip install --pre pyinstaller
if errorlevel 1 (
    echo [FEHLER] PyInstaller-Install fehlgeschlagen.
    echo          PyInstaller-Support für Python 3.15 ist evtl. noch ausstehend.
    echo          Workaround: Build mit Python 3.12 oder 3.13 (siehe README).
    pause
    exit /b 1
)

REM --- Aufräumen -------------------------------------------------------------
echo [4/5] Räume alte Builds auf...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "XPrint-VoiceChanger.spec" del /q "XPrint-VoiceChanger.spec"

REM --- Icon-Handling (optional) ---------------------------------------------
set ICON_FLAG=
if exist "icon.ico" (
    set ICON_FLAG=--icon=icon.ico
    echo       icon.ico gefunden.
) else (
    echo       Kein icon.ico -- Build läuft ohne Custom-Icon.
)

REM --- PyInstaller -----------------------------------------------------------
echo [5/5] Baue .exe ...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "XPrint-VoiceChanger" ^
    %ICON_FLAG% ^
    --collect-all customtkinter ^
    --collect-all pedalboard ^
    --collect-all sounddevice ^
    --collect-binaries pedalboard ^
    --hidden-import=customtkinter ^
    --hidden-import=_cffi_backend ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo.
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    echo         Bei Python 3.15-Alpha sind Hooks evtl. nicht aktuell -
    echo         als Workaround Build mit Python 3.12/3.13 versuchen.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   BUILD OK
echo  ============================================================
echo   Output:    dist\XPrint-VoiceChanger.exe
echo   Installer: Öffne installer.iss mit Inno Setup Compiler
echo              und drücke Strg+F9
echo  ============================================================
echo.

pause
endlocal
