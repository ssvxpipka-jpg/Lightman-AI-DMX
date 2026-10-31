@echo off
REM ============================================================================
REM Lightman - Windows build (PyInstaller exe + Inno Setup Setup.exe).
REM Downloads the GGUF model BEFORE PyInstaller so it's bundled.
REM Ollama is NOT installed anymore.
REM ============================================================================
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "MODEL_DIR=%PROJECT_ROOT%\assets\models"
set "MODEL_FILE=%MODEL_DIR%\qwen2.5-coder-3b-instruct-q4_k_m.gguf"
set "HF_REPO=Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
set "HF_FILE=qwen2.5-coder-3b-instruct-q4_k_m.gguf"

cd /d "%PROJECT_ROOT%"

echo ==^> [1/5] Checking Python
python --version >nul 2>&1
if errorlevel 1 ( echo ERROR: python not in PATH & exit /b 1 )

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install --upgrade pip pyinstaller
)
python -c "import huggingface_hub" >nul 2>&1
if errorlevel 1 (
    echo Installing huggingface_hub...
    python -m pip install --upgrade huggingface_hub
)

echo ==^> [2/5] Ensuring GGUF model is downloaded
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
if not exist "%MODEL_FILE%" (
    echo    Downloading %HF_FILE% ^(~2 GB, one-time^)...
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='%HF_REPO%', filename='%HF_FILE%', local_dir=r'%MODEL_DIR%')"
) else (
    echo    Model already present at %MODEL_FILE%
)

echo ==^> [3/5] Cleaning previous build
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

echo ==^> [4/5] Running PyInstaller
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name Lightman ^
    --collect-all llama_cpp ^
    --collect-all chromadb ^
    --add-data "assets;assets" ^
    --add-data "fixtures_db;fixtures_db" ^
    --add-data "src\director\theme.qss;src\director" ^
    src\director\main.py
if errorlevel 1 ( echo PyInstaller FAILED & exit /b 1 )

echo ==^> [5/5] Inno Setup
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
    echo !! Inno Setup not found. Install from https://jrsoftware.org/isdl.php
    echo    exe: %DIST_DIR%\Lightman\Lightman.exe
    exit /b 0
)
"%ISCC%" "%SCRIPT_DIR%installer_win.iss"
if errorlevel 1 ( echo Inno Setup FAILED & exit /b 1 )

echo.
echo Done.
echo   exe       -^> %DIST_DIR%\Lightman\Lightman.exe
echo   installer -^> %DIST_DIR%\Lightman-Setup.exe
endlocal