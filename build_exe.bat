@echo off
echo ========================================
echo   Color Clicker EXE Build
echo ========================================
echo.

echo [1/2] Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo [2/2] Building EXE...
python -m PyInstaller --onefile --noconsole --name "ColorClicker" color_clicker.py

echo.
echo ========================================
echo   Build Complete!
echo   dist\ColorClicker.exe
echo ========================================
pause
