@echo off
echo Building Midivis...

REM Get the directory where this script is located (project root)
set "PROJECT_ROOT=%~dp0"

REM Install/update requirements
echo Installing requirements...
pip install -r "%PROJECT_ROOT%requirements.txt"

REM Clean previous builds
if exist "%PROJECT_ROOT%dist" rmdir /s /q "%PROJECT_ROOT%dist"
if exist "%PROJECT_ROOT%build" rmdir /s /q "%PROJECT_ROOT%build"

REM Build with PyInstaller
echo Building executable...
cd /d "%PROJECT_ROOT%"
python -m PyInstaller Midivis.spec

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: %PROJECT_ROOT%dist\Midivis.exe
echo.
