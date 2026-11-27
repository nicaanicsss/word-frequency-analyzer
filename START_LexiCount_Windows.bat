@echo off
title LexiCount
cd /d "%~dp0"
rem Find Python 3.10+ (the "py" launcher first, then "python").
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY (
  echo.
  echo  LexiCount needs Python 3.10 or newer, which was not found on this computer.
  echo.
  echo  1. Download Python from https://www.python.org/downloads/
  echo  2. During setup, tick "Add python.exe to PATH".
  echo  3. Double-click START_LexiCount_Windows.bat again.
  echo.
  pause
  exit /b 1
)
%PY% launch.py %*
echo.
pause
