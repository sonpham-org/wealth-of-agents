# MPES Setup Script for Windows
# Run this in PowerShell to set up the project

Write-Host "🚀 MPES Setup Script" -ForegroundColor Cyan
Write-Host "=" * 60

# Check Python
Write-Host "`n📌 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`n📌 Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n📌 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host "`n📌 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`n📌 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env file
Write-Host "`n📌 Setting up environment..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file from template" -ForegroundColor Green
}

# Create output directory
Write-Host "`n📌 Creating output directory..." -ForegroundColor Yellow
if (!(Test-Path "output")) {
    New-Item -ItemType Directory -Path "output" | Out-Null
}
Write-Host "✓ Output directory ready" -ForegroundColor Green

# Summary
Write-Host "`n" + "=" * 60
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`nNext steps:"
Write-Host "  1. Review and edit .env file if needed"
Write-Host "  2. Run demo: python quickstart.py"
Write-Host "  3. Run tests: pytest tests/ -v"
Write-Host "  4. Run custom simulation: python run_simulation.py --help"

Write-Host "`nTo activate the environment in future sessions:"
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan

Write-Host "`n" + "=" * 60
