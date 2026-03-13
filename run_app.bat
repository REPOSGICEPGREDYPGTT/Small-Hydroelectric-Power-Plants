@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
  echo Create it first with: python -m venv .venv
  pause
  exit /b 1
)

set "APP_SCRIPT=%~1"

if "%APP_SCRIPT%"=="" (
  if exist "streamlit_app.py" (
    set "APP_SCRIPT=streamlit_app.py"
  ) else (
    for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$c = Get-ChildItem -File -Filter *.py | Where-Object { Select-String -Path $_.FullName -Pattern 'import streamlit as st|st\.set_page_config' -Quiet }; if($c){$c | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty Name }"`) do set "APP_SCRIPT=%%F"
  )
)

if "%APP_SCRIPT%"=="" (
  echo [ERROR] No Streamlit Python entrypoint was found.
  echo Pass one explicitly, for example: run_app.bat streamlit_app.py
  pause
  exit /b 1
)

if not exist "%APP_SCRIPT%" (
  echo [ERROR] File not found: %APP_SCRIPT%
  pause
  exit /b 1
)

echo Starting Streamlit app...
echo URL: http://localhost:8501
echo Script: %APP_SCRIPT%
echo.

".venv\Scripts\python.exe" -m streamlit run "%APP_SCRIPT%"

endlocal
