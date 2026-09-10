@echo off
REM Aufgabe 6 - taeglicher Lauf der Atrelle Fit-Pipeline (Windows).
REM Schreibt die Fits in fits\JJJJ-MM-TT\. Konfig via COUNT / TRYON.

setlocal
cd /d "%~dp0"

if "%COUNT%"=="" set COUNT=7

REM Datum als YYYY-MM-DD (unabhaengig vom Gebietsschema via PowerShell)
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATE=%%d
set OUT=fits\%DATE%
if not exist logs mkdir logs

python fetch_assets.py  >> "logs\%DATE%.log" 2>&1

if "%TRYON%"=="1" (
  python generate_fits.py --count %COUNT% --out "%OUT%" --tryon >> "logs\%DATE%.log" 2>&1
) else (
  python generate_fits.py --count %COUNT% --out "%OUT%" >> "logs\%DATE%.log" 2>&1
)

echo Fertig. Fits in %OUT%, Log in logs\%DATE%.log
endlocal
