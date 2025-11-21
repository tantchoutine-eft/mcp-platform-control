# MCP Configuration Generator
# Creates personalized MCP configurations with dynamic paths

param(
    [string]$Template = ".\configs\mcp.json",
    [string]$Output,
    [string]$Profile = "aws-sso-primary",
    [string]$Region = "us-east-1",
    [switch]$Interactive,
    [switch]$MultiAccount
)

Write-Host "`n🎨 MCP Configuration Generator" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Dynamic path resolution
$userName = $env:USERNAME
$userProfile = $env:USERPROFILE
$uvPath = "$userProfile\.local\bin\uvx.exe"
$awsConfigPath = "$userProfile\.aws\config"
$awsCredentialsPath = "$userProfile\.aws\credentials"

# Verify UV installation
if (-not (Test-Path $uvPath)) {
    Write-Host "❌ UV not found. Installing..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
}

# Interactive mode
if ($Interactive) {
    Write-Host "`nInteractive Configuration Mode" -ForegroundColor Green
    
    # Select AWS Profile
    Write-Host "`nAvailable AWS Profiles:" -ForegroundColor Cyan
    $profiles = @(
        "aws-sso-primary (Management - 886089548523)",
        "aws-sso-sandbox (Sandbox - 537124940140)",
        "aws-sso-nonprod (NonProd - 381492229443)",
        "aws-sso-prod (Production - 654654560452)",
        "aws-sso-security (Security - 131087618144)",
        "aws-sso-infrastructure (Infrastructure - 211125547824)",
        "aws-sso-logs (Logs - 213611281426)"
    )
    
    for ($i = 0; $i -lt $profiles.Length; $i++) {
        Write-Host "  $($i + 1). $($profiles[$i])"
    }
    
    $selection = Read-Host "`nSelect default profile (1-$($profiles.Length))"
    $Profile = $profiles[$selection - 1].Split(' ')[0]
    
    # Select Region
    Write-Host "`nCommon AWS Regions:" -ForegroundColor Cyan
    $regions = @("us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1")
    for ($i = 0; $i -lt $regions.Length; $i++) {
        Write-Host "  $($i + 1). $($regions[$i])"
    }
    
    $regionSelection = Read-Host "`nSelect region (1-$($regions.Length))"
    $Region = $regions[$regionSelection - 1]
    
    # Multi-account option
    $multiChoice = Read-Host "`nEnable multi-account configuration? (Y/N)"
    $MultiAccount = ($multiChoice -eq 'Y' -or $multiChoice -eq 'y')
}

# Load template
if (Test-Path $Template) {
    $config = Get-Content $Template -Raw | ConvertFrom-Json
} else {
    Write-Host "Creating new configuration from scratch..." -ForegroundColor Yellow
    $config = @{ mcpServers = @{} } | ConvertTo-Json | ConvertFrom-Json
}

# Function to update server configuration
function Update-ServerConfig {
    param($Server, $Name)
    
    # Update command path
    if ($Server.command -like "*uvx.exe*") {
        $Server.command = $uvPath
    }
    
    # Update environment variables
    if ($Server.env) {
        $Server.env.AWS_PROFILE = $Profile
        $Server.env.AWS_REGION = $Region
        $Server.env.AWS_CONFIG_FILE = $awsConfigPath
        $Server.env.AWS_SHARED_CREDENTIALS_FILE = $awsCredentialsPath
        $Server.env.FASTMCP_LOG_LEVEL = "ERROR"
    } else {
        $Server | Add-Member -MemberType NoteProperty -Name "env" -Value @{
            AWS_PROFILE = $Profile
            AWS_REGION = $Region
            AWS_CONFIG_FILE = $awsConfigPath
            AWS_SHARED_CREDENTIALS_FILE = $awsCredentialsPath
            FASTMCP_LOG_LEVEL = "ERROR"
        } -Force
    }
    
    # Ensure required properties
    if (-not $Server.autoApprove) {
        $Server | Add-Member -MemberType NoteProperty -Name "autoApprove" -Value @() -Force
    }
    if (-not $Server.disabled) {
        $Server | Add-Member -MemberType NoteProperty -Name "disabled" -Value $false -Force
    }
    
    return $Server
}

# Process each server
Write-Host "`nProcessing servers..." -ForegroundColor Cyan
foreach ($serverName in $config.mcpServers.PSObject.Properties.Name) {
    if ($serverName -notlike "//*") {  # Skip comment entries
        Write-Host "  📦 $serverName" -NoNewline
        $config.mcpServers.$serverName = Update-ServerConfig -Server $config.mcpServers.$serverName -Name $serverName
        Write-Host " ✅" -ForegroundColor Green
    }
}

# Add multi-account servers if requested
if ($MultiAccount) {
    Write-Host "`nAdding multi-account servers..." -ForegroundColor Cyan
    
    $accounts = @(
        @{Name="sandbox"; Profile="aws-sso-sandbox"},
        @{Name="nonprod"; Profile="aws-sso-nonprod"},
        @{Name="prod"; Profile="aws-sso-prod"},
        @{Name="security"; Profile="aws-sso-security"},
        @{Name="infrastructure"; Profile="aws-sso-infrastructure"},
        @{Name="logs"; Profile="aws-sso-logs"}
    )
    
    foreach ($account in $accounts) {
        $serverName = "aws-api-$($account.Name)"
        Write-Host "  📦 $serverName" -NoNewline
        
        $newServer = @{
            command = $uvPath
            args = @("awslabs.aws-api-mcp-server@latest")
            env = @{
                AWS_PROFILE = $account.Profile
                AWS_REGION = $Region
                AWS_CONFIG_FILE = $awsConfigPath
                AWS_SHARED_CREDENTIALS_FILE = $awsCredentialsPath
                FASTMCP_LOG_LEVEL = "ERROR"
            }
            disabled = $false
            autoApprove = @()
        }
        
        $config.mcpServers | Add-Member -MemberType NoteProperty -Name $serverName -Value $newServer -Force
        Write-Host " ✅" -ForegroundColor Green
    }
}

# Add optimization features
$optimizationConfig = @{
    "__metadata" = @{
        generated = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        generator = "MCP Configuration Generator v2.0"
        user = $userName
        profile = $Profile
        region = $Region
    }
}

$config | Add-Member -MemberType NoteProperty -Name "metadata" -Value $optimizationConfig -Force

# Determine output path
if (-not $Output) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Output = ".\configs\generated\mcp-$timestamp.json"
}

# Ensure output directory exists
$outputDir = Split-Path $Output -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
}

# Save configuration
$config | ConvertTo-Json -Depth 10 | Set-Content $Output -Encoding UTF8
Write-Host "`n✅ Configuration generated successfully!" -ForegroundColor Green
Write-Host "📄 Saved to: $Output" -ForegroundColor Cyan

# Validation
Write-Host "`nValidating generated configuration..." -ForegroundColor Yellow
$validationErrors = @()

# Check if all paths exist
if (-not (Test-Path $uvPath)) {
    $validationErrors += "UV executable not found at $uvPath"
}
if (-not (Test-Path $awsConfigPath)) {
    $validationErrors += "AWS config not found at $awsConfigPath"
}

if ($validationErrors.Count -eq 0) {
    Write-Host "✅ Configuration is valid!" -ForegroundColor Green
    
    Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Copy to Cursor: Copy-Item '$Output' '$userProfile\.cursor\mcp.json'"
    Write-Host "  2. Restart Cursor IDE"
    Write-Host "  3. Run validation: .\scripts\validate-configuration.ps1"
} else {
    Write-Host "⚠️ Validation warnings:" -ForegroundColor Yellow
    $validationErrors | ForEach-Object { Write-Host "  • $_" }
}

# Option to immediately apply
Write-Host "`nApply this configuration to Cursor now? (Y/N): " -NoNewline -ForegroundColor Cyan
$apply = Read-Host
if ($apply -eq 'Y' -or $apply -eq 'y') {
    $cursorConfig = "$userProfile\.cursor\mcp.json"
    
    # Backup existing config
    if (Test-Path $cursorConfig) {
        $backupPath = "$userProfile\.cursor\mcp.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
        Copy-Item $cursorConfig $backupPath
        Write-Host "📦 Backed up existing config to: $backupPath" -ForegroundColor Gray
    }
    
    # Apply new config
    Copy-Item $Output $cursorConfig -Force
    Write-Host "✅ Configuration applied! Please restart Cursor IDE." -ForegroundColor Green
}
