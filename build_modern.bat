@echo off
cd /d "%~dp0"
echo ========================================
echo   Wonryeol Helper Build
echo ========================================
echo.

echo [1/3] Installing requirements...
python -m pip install -r requirements.txt

echo.
echo [2/3] Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo [3/3] Building EXE...
python -m PyInstaller --onefile --noconsole --name "Wonryeol_Helper" ^
    --hidden-import=numpy ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=customtkinter ^
    --hidden-import=mss ^
    --hidden-import=app ^
    --hidden-import=constants ^
    --hidden-import=features ^
    --hidden-import=features.belial ^
    --hidden-import=features.inventory ^
    --hidden-import=features.discard ^
    --hidden-import=features.sell ^
    --hidden-import=features.consume ^
    --hidden-import=features.consume2 ^
    --hidden-import=features.skill_auto ^
    --hidden-import=features.quick_button ^
    --hidden-import=ui ^
    --hidden-import=ui.overlay ^
    --hidden-import=ui.main_window ^
    --hidden-import=utils ^
    --hidden-import=utils.updater ^
    main.py

echo.
echo ========================================
echo   Build Complete!
echo   dist\Wonryeol_Helper.exe
echo ========================================
pause
