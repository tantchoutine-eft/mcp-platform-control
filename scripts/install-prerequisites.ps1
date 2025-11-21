# MCP Prerequisites Installation Script
# This script installs all required components for MCP servers

Write-Host "MCP Prerequisites Installation" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check and install UV package manager
Write-Host "`nChecking for UV package manager..." -ForegroundColor Yellow
if (Test-Command "uv") {
    Write-Host "✓ UV is already installed" -ForegroundColor Green
    uv --version
} else {
    Write-Host "Installing UV package manager..." -ForegroundColor Cyan
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Add to PATH for current session
    $env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
    Write-Host "✓ UV installed successfully" -ForegroundColor Green
}

# Install Python 3.13
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
$uvPath = "C:\Users\$env:USERNAME\.local\bin\uv.exe"
if (Test-Path $uvPath) {
    & $uvPath python list | Select-String "3.13"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python 3.13 is already installed" -ForegroundColor Green
    } else {
        Write-Host "Installing Python 3.13..." -ForegroundColor Cyan
        & $uvPath python install 3.13
        Write-Host "✓ Python 3.13 installed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "UV not found in expected location. Please restart PowerShell and try again." -ForegroundColor Red
}

# Check AWS CLI
Write-Host "`nChecking AWS CLI..." -ForegroundColor Yellow
if (Test-Command "aws") {
    Write-Host "✓ AWS CLI is installed" -ForegroundColor Green
    aws --version
} else {
    Write-Host "⚠ AWS CLI not found. Please install from: https://aws.amazon.com/cli/" -ForegroundColor Red
}

# Check Docker (optional, for containerized MCP servers)
Write-Host "`nChecking Docker (optional)..." -ForegroundColor Yellow
if (Test-Command "docker") {
    Write-Host "✓ Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "ℹ Docker not installed (optional for containerized servers)" -ForegroundColor Gray
}

# Test MCP server packages
Write-Host "`nTesting MCP server packages..." -ForegroundColor Yellow
$servers = @(
    "awslabs.core-mcp-server",
    "awslabs.cdk-mcp-server",
    "awslabs.aws-pricing-mcp-server",
    "awslabs.aws-api-mcp-server",
    "awslabs.bedrock-kb-retrieval-mcp-server",
    "awslabs.nova-canvas-mcp-server",
    "awslabs.mysql-mcp-server"
)

foreach ($server in $servers) {
    Write-Host "  Checking $server..." -NoNewline
    $testResult = & $uvPath run $server@latest --help 2>&1 | Select-String "usage:"
    if ($testResult) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

Write-Host "`n==============================" -ForegroundColor Green
Write-Host "Prerequisites check complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Copy MCP configuration to Cursor:"
Write-Host "   Copy-Item .\configs\mcp.json C:\Users\$env:USERNAME\.cursor\mcp.json"
Write-Host "2. Login to AWS SSO:"
Write-Host "   aws sso login --profile aws-sso-primary"
Write-Host "3. Restart Cursor IDE"
