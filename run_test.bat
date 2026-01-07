@echo off
REM Quick test script for MPES
REM Double-click this file or run from command prompt

echo.
echo ================================================================
echo MPES QUICK TEST
echo ================================================================
echo.

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Conda not found. Please install Anaconda or Miniconda.
    echo.
    pause
    exit /b 1
)

echo Step 1: Activating conda environment...
call conda activate econ_sim
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Environment 'econ_sim' not found.
    echo Please run setup_conda.ps1 first.
    echo.
    pause
    exit /b 1
)

echo Step 2: Running installation test...
echo.
python test_installation.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Some tests failed. Check output above.
    echo.
)

echo.
echo Step 3: Running quick demo...
echo.
python quickstart.py

echo.
echo ================================================================
echo TEST COMPLETE
echo ================================================================
echo.
echo Check the files created:
dir /b simulation_results_*.json 2>nul
echo.
echo Next: Try 'python run_simulation.py --preset small'
echo.
pause
