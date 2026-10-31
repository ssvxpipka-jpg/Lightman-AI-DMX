@echo off
REM ============================================================================
REM Lightman Light — Windows build (PyInstaller .exe + Inno Setup Setup.exe)
REM ============================================================================
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "APP_NAME=LightmanLight"

cd /d "%PROJECT_ROOT%"

echo ==^> [1/5] Checking Python
python --version >nul 2>&1
if errorlevel 1 ( echo ERROR: python not in PATH & exit /b 1 )

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install --upgrade pip pyinstaller
)
python -c "import pythonosc" >nul 2>&1
if errorlevel 1 (
    echo Installing console bridge dependencies...
    python -m pip install --upgrade python-osc requests
)

echo ==^> [2/5] Cleaning previous build
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

echo ==^> [3/5] Running PyInstaller
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "%APP_NAME%" ^
    --collect-all pythonosc ^
    --collect-all requests ^
    --add-data "shared;shared" ^
    --add-data "src\director\theme.qss;src\director" ^
    --add-data "assets;assets" ^
    src\light\main.py
if errorlevel 1 ( echo PyInstaller FAILED & exit /b 1 )

echo ==^> [4/5] Checking Inno Setup
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo !! Inno Setup not found. Install from https://jrsoftware.org/isdl.php
    echo    exe: %DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
    exit /b 0
)

echo ==^> [5/5] Building installer with Inno Setup
"%ISCC%" "%SCRIPT_DIR%installer_light_win.iss"
if errorlevel 1 ( echo Inno Setup FAILED & exit /b 1 )

echo.
echo Done.
echo   exe       -^> %DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
echo   installer -^> %DIST_DIR%\%APP_NAME%-Setup.exe
endlocal