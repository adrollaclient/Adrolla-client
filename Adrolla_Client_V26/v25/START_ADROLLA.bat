@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Adrolla Client - Start

echo.
echo  ============================================
echo             ADROLLA CLIENT
echo  ============================================
echo.

set "PYCMD="
call :find_python
if defined PYCMD goto run

echo Python wurde nicht gefunden (oder Tkinter fehlt).
echo Die neueste Python-Version wird jetzt automatisch installiert.
echo Das passiert nur beim ersten Start und dauert einige Minuten.
echo Bitte das Fenster offen lassen.
echo.
del "%TEMP%\adrolla_py.txt" >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_python.ps1" -OutFile "%TEMP%\adrolla_py.txt"
if errorlevel 1 goto pyfail
if not exist "%TEMP%\adrolla_py.txt" goto pyfail
set /p PYCMD=<"%TEMP%\adrolla_py.txt"
del "%TEMP%\adrolla_py.txt" >nul 2>nul
if not defined PYCMD goto pyfail
"%PYCMD%" -c "import tkinter" >nul 2>nul
if errorlevel 1 goto pyfail

:run
echo Verwende Python: %PYCMD%
"%PYCMD%" -m pip install --user -r requirements.txt
if errorlevel 1 goto pipfail
"%PYCMD%" main.py
if not errorlevel 1 goto finished
echo.
echo Adrolla konnte nicht gestartet werden.
echo Pruefe die Fehlermeldung oben.
goto failed

:pyfail
echo.
echo Python konnte nicht automatisch installiert werden.
echo Pruefe deine Internetverbindung oder installiere Python 3 selbst:
echo https://www.python.org/downloads/
echo Aktiviere beim Setup "Add Python to PATH".
start "" "https://www.python.org/downloads/"
goto failed

:pipfail
echo.
echo Die Minecraft-Startkomponente konnte nicht installiert werden.
echo Pruefe deine Internetverbindung und versuche es erneut.
goto failed

:finished
echo.
echo Adrolla wurde geschlossen.
goto end

:failed
echo.
echo Falls das Problem bleibt, sende ein Foto dieser Fehlermeldung.
pause
:end
endlocal
exit /b 0

:find_python
set "PYCMD="
where py >nul 2>nul
if not errorlevel 1 for /f "usebackq delims=" %%P in (`py -3 -c "import sys, tkinter; print(sys.executable)" 2^>nul`) do if not defined PYCMD set "PYCMD=%%P"
if defined PYCMD exit /b 0
for /f "delims=" %%A in ('where python 2^>nul') do if not defined PYCMD "%%A" -c "import tkinter" >nul 2>nul && set "PYCMD=%%A"
if defined PYCMD exit /b 0
for /f "delims=" %%D in ('dir /b /ad /o-n "%LOCALAPPDATA%\Programs\Python" 2^>nul') do if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\%%D\python.exe" "%LOCALAPPDATA%\Programs\Python\%%D\python.exe" -c "import tkinter" >nul 2>nul && set "PYCMD=%LOCALAPPDATA%\Programs\Python\%%D\python.exe"
exit /b 0
