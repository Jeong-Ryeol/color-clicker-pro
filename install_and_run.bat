@echo off
cd /d "%~dp0"
echo Installing required libraries...
python -m pip install pyautogui keyboard pillow pywin32 customtkinter mss numpy
echo.
echo Starting program...
python color_clicker_modern.py
pause
