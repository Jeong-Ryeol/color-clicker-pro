@echo off
cd /d "%~dp0"
echo ========================================
echo   Color Clicker Pro (Modern UI) Build
echo ========================================
echo.

echo [1/3] Installing requirements...
python -m pip install -r requirements.txt

echo.
echo [2/3] Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo [3/3] Building EXE...
python -m PyInstaller --onefile --noconsole --name "ColorClickerPro" --hidden-import=numpy --hidden-import=PIL._tkinter_finder color_clicker_modern.py

echo.
echo ========================================
echo   Build Complete!
echo   dist\ColorClickerPro.exe
echo ========================================
pause
