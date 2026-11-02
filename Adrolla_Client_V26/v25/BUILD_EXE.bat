@echo off
cd /d "%~dp0"
title Adrolla Client - EXE Builder
where py >nul 2>nul
if errorlevel 1 (
  echo Python wurde nicht gefunden. Bitte Python 3 installieren.
  pause
  exit /b 1
)
py -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto error
py -m pip install -r requirements.txt
if errorlevel 1 goto error
py -m PyInstaller --noconfirm --clean --windowed --name AdrollaClient --icon "saturn.ico" --add-data "config.json;." --add-data "saturn.ico;." --add-data "saturn.png;." --add-data "minecraft_theme;minecraft_theme" --hidden-import PIL.ImageTk main.py
if errorlevel 1 goto error
copy /Y config.json dist\config.json >nul
echo.
echo Fertig! Die EXE liegt im Ordner dist.
pause
exit /b 0
:error
echo.
echo Build fehlgeschlagen. Bitte die Fehlermeldung oben pruefen.
pause
exit /b 1
