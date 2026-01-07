# MPES Conda Setup and Test Script
# Run this in PowerShell to set up and test the project

param(
    [switch]$SkipTest
)

Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "MPES CONDA SETUP & TEST" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Step 1: Check conda
Write-Host "Step 1: Checking Conda..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version 2>&1
    Write-Host "  ✓ $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Conda not found. Please install Anaconda or Miniconda" -ForegroundColor Red
    exit 1
}

# Step 2: Create environment
Write-Host "`nStep 2: Creating conda environment..." -ForegroundColor Yellow
$envExists = conda env list | Select-String "econ_sim"
if ($envExists) {
    Write-Host "  ℹ Environment 'econ_sim' already exists" -ForegroundColor Blue
    $response = Read-Host "  Remove and recreate? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "  Removing old environment..." -ForegroundColor Yellow
        conda env remove -n econ_sim -y
        Write-Host "  Creating new environment..." -ForegroundColor Yellow
        conda create -n econ_sim python=3.11 -y
        Write-Host "  ✓ Environment created" -ForegroundColor Green
    } else {
        Write-Host "  Using existing environment" -ForegroundColor Yellow
    }
} else {
    conda create -n econ_sim python=3.11 -y
    Write-Host "  ✓ Environment created" -ForegroundColor Green
}

# Step 3: Activate and install dependencies
Write-Host "`nStep 3: Installing dependencies..." -ForegroundColor Yellow
Write-Host "  (This may take a few minutes)" -ForegroundColor Gray

# Note: We need to run commands in the conda environment
$installScript = @"
conda activate econ_sim
pip install -r requirements.txt
"@

$installScript | Out-File -FilePath "temp_install.ps1" -Encoding ASCII
& conda run -n econ_sim pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Installation failed" -ForegroundColor Red
    exit 1
}

# Step 4: Run tests
if (-not $SkipTest) {
    Write-Host "`nStep 4: Running installation tests..." -ForegroundColor Yellow
    Write-Host "  (This will verify everything works)" -ForegroundColor Gray
    Write-Host ""
    
    & conda run -n econ_sim python test_installation.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n  ✓ All tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`n  ⚠ Some tests failed - check output above" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nStep 4: Skipping tests (use without -SkipTest to run)" -ForegroundColor Gray
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nTo activate the environment:" -ForegroundColor Yellow
Write-Host "  conda activate econ_sim" -ForegroundColor White

Write-Host "`nQuick test commands:" -ForegroundColor Yellow
Write-Host "  python quickstart.py                    # Interactive demo" -ForegroundColor White
Write-Host "  python run_simulation.py --preset small # Quick test" -ForegroundColor White
Write-Host "  pytest tests/ -v                        # Run test suite" -ForegroundColor White

Write-Host "`nWith visualization:" -ForegroundColor Yellow
Write-Host "  python run_simulation.py --websocket --preset inflation" -ForegroundColor White
Write-Host "  Then open: frontend\index.html in browser" -ForegroundColor Gray

Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
