@echo off
echo ================================
echo TXT to EPUB Converter - Windows
echo ================================
echo.

REM Check if conda is installed
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Conda is not installed or not in PATH!
    echo Please install Anaconda or Miniconda first:
    echo https://www.anaconda.com/products/distribution
    echo https://docs.conda.io/en/latest/miniconda.html
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking conda installation... OK
echo.

REM Check if environment exists
conda info --envs | findstr "txt-to-epub" >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/4] Creating conda environment...
    conda create -n txt-to-epub python=3.10 -y
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create conda environment!
        pause
        exit /b 1
    )
    echo Environment created successfully!
    echo Activating new environment...
    call conda activate txt-to-epub
    if %errorlevel% neq 0 (
        echo ERROR: Failed to activate newly created environment!
        pause
        exit /b 1
    )
) else (
    echo [2/4] Conda environment already exists... OK
    echo Activating existing environment...
    call conda activate txt-to-epub
    if %errorlevel% neq 0 (
        echo ERROR: Failed to activate existing environment!
        pause
        exit /b 1
    )
)
echo.

REM Install dependencies
echo [3/4] Installing dependencies...

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Run the application
echo [4/4] Starting TXT to EPUB Converter...
echo.
echo The application will open in your default web browser.
echo Press Ctrl+C to stop the application.
echo.
python webui.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start!
    pause
) 