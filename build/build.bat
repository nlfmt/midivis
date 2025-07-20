@echo off
echo Building Audio Input Streamer...

REM Check if icon.ico exists
if not exist "..\assets\icons\icon.ico" (
    echo WARNING: icon.ico not found. Please convert icon.svg to icon.ico first.
    echo You can use online converters or tools like Inkscape to convert SVG to ICO.
    pause
    exit /b 1
)

REM Install/update requirements
echo Installing requirements...
pip install -r ..\requirements.txt

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
echo Building executable...
pyinstaller AudioInputStreamer.spec

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\AudioInputStreamer.exe
echo.
pause
