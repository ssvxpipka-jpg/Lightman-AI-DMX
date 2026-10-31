@echo off
REM ==========================================
REM   Lightman Installation Script (Windows)
REM ==========================================
REM Checks: Python 3.10+, creates venv, installs all dependencies.

echo.
echo ==========================================
echo   Lightman - Stage Lighting Automation 
echo   Installation Script (Windows)          
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3 is not installed or not in PATH.
    pause
    exit /b 1
)
echo Using Python:
python --version

REM Check Python version (3.10+)
for /f "tokens=2 delims=." %%i in ('python --version') do (
    set PY_MAJOR=%%i
    for /f "tokens=*" %%j in ("%%i") do set PY_MINOR=%%j
)
REM Simpler version check using Python itself
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3.10+ required.
    pause
    exit /b 1
)
echo Python version OK (3.10+)

REM ─── Ollama Auto-Install ─────────────────────────────────────────────
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama not found. Installing via winget...
    winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements
)
echo Pulling Qwen model...
ollama pull qwen2.5-coder:3b

REM Create virtual environment
set VENV_DIR=venv
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Check if PySide6 installed successfully
python -c "import PySide6" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==========================================
    echo   WARNING: PySide6 failed to install!
    echo ==========================================
    echo PySide6^>^=6.10.0 requires Python 3.10+ and may
    echo not be available for Python 3.14 on all platforms.
    echo If installation fails, please install Python 3.12
    echo and re-run this installer.
    echo ==========================================
)

echo.
echo ==========================================
echo   Installation completed successfully! 
echo ==========================================
echo.
echo To activate the environment, run:
echo   venv\Scripts\activate.bat
echo.
echo Then run the Director:
echo   python -m src.director.main
echo.

pause
