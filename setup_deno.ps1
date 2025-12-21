# Deno Setup Script for Yard
# Downloads and extracts Deno runtime automatically

$DENO_VERSION = "latest"
$DENO_URL = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
$BIN_DIR = Join-Path $PSScriptRoot "src\bin"
$DENO_ZIP = Join-Path $BIN_DIR "deno.zip"
$DENO_EXE = Join-Path $BIN_DIR "deno.exe"

Write-Host "Setting up Deno runtime for Yard..." -ForegroundColor Cyan

# Create bin directory if it doesn't exist
if (-not (Test-Path $BIN_DIR)) {
    New-Item -ItemType Directory -Path $BIN_DIR | Out-Null
    Write-Host "Created src/bin directory" -ForegroundColor Green
}

# Check if Deno already exists
if (Test-Path $DENO_EXE) {
    Write-Host "Deno is already installed at: $DENO_EXE" -ForegroundColor Green
    & $DENO_EXE --version
    
    $response = Read-Host "Do you want to re-download? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Setup complete!" -ForegroundColor Green
        exit 0
    }
    Remove-Item $DENO_EXE -Force
}

# Download Deno
Write-Host "Downloading Deno from GitHub..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $DENO_URL -OutFile $DENO_ZIP -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green
} catch {
    Write-Host "Failed to download Deno: $_" -ForegroundColor Red
    exit 1
}

# Extract Deno
Write-Host "Extracting deno.exe..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $DENO_ZIP -DestinationPath $BIN_DIR -Force
    Remove-Item $DENO_ZIP -Force
    Write-Host "Extraction complete!" -ForegroundColor Green
} catch {
    Write-Host "Failed to extract Deno: $_" -ForegroundColor Red
    exit 1
}

# Verify installation
if (Test-Path $DENO_EXE) {
    Write-Host "`nDeno successfully installed!" -ForegroundColor Green
    Write-Host "Location: $DENO_EXE" -ForegroundColor Cyan
    Write-Host "`nVersion info:" -ForegroundColor Cyan
    & $DENO_EXE --version
} else {
    Write-Host "Installation failed - deno.exe not found!" -ForegroundColor Red
    exit 1
}
