@echo off
REM ============================================================================
REM  X-Print Voice Changer - Build Script
REM ----------------------------------------------------------------------------
REM  Erstellt dist\XPrint-VoiceChanger.exe als single-file Windows-Executable.
REM  Benoetigt Python 3.11 64-bit im PATH.
REM ============================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ============================================================
echo   X-PRINT // VOICE CHANGER  --  BUILD
echo  ============================================================
echo.

REM --- Python-Check ----------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht im PATH gefunden.
    echo         Installiere Python 3.11 64-bit von python.org
    pause
    exit /b 1
)

REM --- Venv (optional, sauberer Build) ---------------------------------------
if not exist "venv" (
    echo [1/5] Erstelle virtuelle Umgebung...
    python -m venv venv
    if errorlevel 1 (
        echo [FEHLER] venv konnte nicht erstellt werden.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

REM --- Dependencies ----------------------------------------------------------
echo [2/5] Installiere Dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [FEHLER] Dependencies-Install fehlgeschlagen.
    pause
    exit /b 1
)

echo [3/5] Installiere PyInstaller...
python -m pip install pyinstaller==6.11.1
if errorlevel 1 (
    echo [FEHLER] PyInstaller-Install fehlgeschlagen.
    pause
    exit /b 1
)

REM --- Aufraeumen ------------------------------------------------------------
echo [4/5] Raeume alte Builds auf...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "XPrint-VoiceChanger.spec" del /q "XPrint-VoiceChanger.spec"

REM --- Icon-Handling (optional) ---------------------------------------------
set ICON_FLAG=
if exist "icon.ico" (
    set ICON_FLAG=--icon=icon.ico
    echo       icon.ico gefunden.
) else (
    echo       Kein icon.ico -- Build laeuft ohne Custom-Icon.
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
    --hidden-import=customtkinter ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo.
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   BUILD OK
echo  ============================================================
echo   Output:  dist\XPrint-VoiceChanger.exe
echo.
echo   Installer:  Oeffne installer.iss mit Inno Setup Compiler
echo               und klicke 'Build / Compile'  (Strg+F9)
echo  ============================================================
echo.

pause
endlocal
