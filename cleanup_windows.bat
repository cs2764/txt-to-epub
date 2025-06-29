@echo off
echo ========================================
echo TXT to EPUB Converter - Environment cleanup
echo ========================================
echo.

REM Check if conda is installed
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Conda is not installed or not in PATH!
    echo Cannot proceed with cleanup.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking conda installation... OK
echo.

REM Check if environment exists
conda info --envs | findstr "txt-to-epub" >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/3] Environment 'txt-to-epub' not found.
    echo Nothing to clean up.
    echo.
    pause
    exit /b 0
)

echo [2/3] Found environment 'txt-to-epub'
echo.

REM Show environment info
echo Environment details:
conda info --envs | findstr "txt-to-epub"
echo.

REM Ask for confirmation
echo WARNING: This will permanently delete the 'txt-to-epub' conda environment!
echo This action cannot be undone.
echo.
set /p confirm="Are you sure you want to continue? (y/N): "

if /i not "%confirm%"=="y" if /i not "%confirm%"=="yes" (
    echo Cleanup cancelled by user.
    echo.
    pause
    exit /b 0
)

echo.
echo [3/3] Removing conda environment...

REM Remove the environment
conda env remove -n txt-to-epub -y
if %errorlevel% neq 0 (
    echo ERROR: Failed to remove conda environment!
    echo You may need to deactivate the environment first if it's currently active.
    echo Try running: conda deactivate
    echo.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Environment 'txt-to-epub' has been completely removed!
echo.
echo Cleanup completed successfully.
echo You can now safely delete this project folder if you no longer need it.
echo.
pause 