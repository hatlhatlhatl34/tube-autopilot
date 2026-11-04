@echo off
title tube-autopilot - setup wizard
cd /d "%~dp0"
echo.
echo   tube-autopilot SETUP WIZARD
echo   ---------------------------
echo   If nothing happens, install Python from https://www.python.org/downloads/
echo   (tick "Add python.exe to PATH" during install), then double-click this
echo   file again.
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\setup_wizard.py
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python tools\setup_wizard.py
  goto :end
)
echo   Python was not found on this computer. Install it first:
echo   https://www.python.org/downloads/
:end
echo.
pause
