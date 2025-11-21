# MCP Configuration Validator
# Comprehensive validation of MCP setup and configurations

param(
    [switch]$Verbose,
    [switch]$AutoFix,
    [string]$ConfigPath = "$env:USERPROFILE\.cursor\mcp.json"
)

$ErrorActionPreference = "Stop"
$script:issues = @()
$script:warnings = @()
$script:fixes = @()

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     MCP Configuration Validator v2.0     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan

function Test-Requirement {
    param($Name, $TestScript, $FixScript, $IsCritical = $true)
    
    Write-Host "`n🔍 Checking $Name..." -NoNewline
    try {
        $result = & $TestScript
        if ($result) {
            Write-Host " ✅" -ForegroundColor Green
            return $true
        }
    } catch {
        $errorMsg = $_.Exception.Message
    }
    
    if ($IsCritical) {
        Write-Host " ❌" -ForegroundColor Red
        $script:issues += "$Name : $errorMsg"
    } else {
        Write-Host " ⚠️" -ForegroundColor Yellow
        $script:warnings += "$Name : $errorMsg"
    }
    
    if ($AutoFix -and $FixScript) {
        Write-Host "   🔧 Attempting auto-fix..." -ForegroundColor Yellow
        try {
            & $FixScript
            $script:fixes += "Fixed: $Name"
            Write-Host "   ✅ Fixed!" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "   ❌ Auto-fix failed: $_" -ForegroundColor Red
        }
    }
    return $false
}

# 1. Check UV installation
Test-Requirement "UV Package Manager" {
    Get-Command "C:\Users\$env:USERNAME\.local\bin\uv.exe" -ErrorAction Stop
    return $true
} {
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
}

# 2. Check Python 3.13
Test-Requirement "Python 3.13" {
    $pythonList = & "C:\Users\$env:USERNAME\.local\bin\uv.exe" python list 2>&1
    return $pythonList -match "3\.13"
} {
    & "C:\Users\$env:USERNAME\.local\bin\uv.exe" python install 3.13
}

# 3. Check AWS CLI
Test-Requirement "AWS CLI" {
    Get-Command aws -ErrorAction Stop
    return $true
} {
    Start-Process "https://aws.amazon.com/cli/"
    Write-Host "Please install AWS CLI manually from the opened webpage"
}

# 4. Validate MCP Configuration File
Test-Requirement "MCP Configuration File" {
    if (Test-Path $ConfigPath) {
        $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        return $config.mcpServers -ne $null
    }
    return $false
} {
    $projectConfig = ".\configs\mcp.json"
    if (Test-Path $projectConfig) {
        Copy-Item $projectConfig $ConfigPath -Force
    }
}

# 5. Check AWS SSO Sessions
Write-Host "`n📊 AWS Account Access Status:" -ForegroundColor Cyan
$profiles = @(
    @{Name="Management"; Profile="aws-sso-primary"; AccountId="886089548523"},
    @{Name="Sandbox"; Profile="aws-sso-sandbox"; AccountId="537124940140"},
    @{Name="NonProd"; Profile="aws-sso-nonprod"; AccountId="381492229443"},
    @{Name="Production"; Profile="aws-sso-prod"; AccountId="654654560452"},
    @{Name="Security"; Profile="aws-sso-security"; AccountId="131087618144"},
    @{Name="Infrastructure"; Profile="aws-sso-infrastructure"; AccountId="211125547824"},
    @{Name="Logs"; Profile="aws-sso-logs"; AccountId="213611281426"}
)

$accessibleAccounts = 0
foreach ($account in $profiles) {
    Write-Host "  $($account.Name.PadRight(15))" -NoNewline
    $identity = aws sts get-caller-identity --profile $account.Profile 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Active" -ForegroundColor Green
        $accessibleAccounts++
    } else {
        Write-Host "⭕ Needs login" -ForegroundColor Yellow
    }
}

# 6. Test MCP Server Packages
Write-Host "`n🔌 MCP Server Package Status:" -ForegroundColor Cyan
$servers = @(
    @{Name="AWS Core"; Package="awslabs.core-mcp-server@latest"},
    @{Name="AWS CDK"; Package="awslabs.cdk-mcp-server@latest"},
    @{Name="AWS Pricing"; Package="awslabs.aws-pricing-mcp-server@latest"},
    @{Name="AWS API"; Package="awslabs.aws-api-mcp-server@latest"},
    @{Name="Bedrock KB"; Package="awslabs.bedrock-kb-retrieval-mcp-server@latest"},
    @{Name="Nova Canvas"; Package="awslabs.nova-canvas-mcp-server@latest"},
    @{Name="MySQL Aurora"; Package="awslabs.mysql-mcp-server@latest"}
)

$uvx = "C:\Users\$env:USERNAME\.local\bin\uvx.exe"
foreach ($server in $servers) {
    Write-Host "  $($server.Name.PadRight(15))" -NoNewline
    $test = & $uvx $server.Package --help 2>&1 | Select-String "usage:" -Quiet
    if ($test) {
        Write-Host "✅ Ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Needs attention" -ForegroundColor Yellow
        $script:warnings += "$($server.Name) package may need reinstallation"
    }
}

# 7. Network Connectivity Tests
Write-Host "`n🌐 Network Connectivity:" -ForegroundColor Cyan
$endpoints = @(
    @{Name="AWS SSO"; Endpoint="sts.amazonaws.com"; Port=443},
    @{Name="Aurora MySQL"; Endpoint="expanseft-prototype.c32erjvbancm.us-east-1.rds.amazonaws.com"; Port=3306},
    @{Name="AWS API"; Endpoint="ec2.amazonaws.com"; Port=443}
)

foreach ($endpoint in $endpoints) {
    Write-Host "  $($endpoint.Name.PadRight(15))" -NoNewline
    $test = Test-NetConnection $endpoint.Endpoint -Port $endpoint.Port -WarningAction SilentlyContinue
    if ($test.TcpTestSucceeded) {
        Write-Host "✅ Connected" -ForegroundColor Green
    } else {
        Write-Host "❌ Unreachable" -ForegroundColor Red
        $script:issues += "Cannot reach $($endpoint.Name) at $($endpoint.Endpoint):$($endpoint.Port)"
    }
}

# 8. Configuration Optimization Check
Write-Host "`n⚙️ Configuration Optimization:" -ForegroundColor Cyan
if (Test-Path $ConfigPath) {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $optimizations = @()
    
    foreach ($serverName in $config.mcpServers.PSObject.Properties.Name) {
        $server = $config.mcpServers.$serverName
        if ($server.env -and -not $server.env.FASTMCP_LOG_LEVEL) {
            $optimizations += "$serverName: Add FASTMCP_LOG_LEVEL=ERROR for better performance"
        }
    }
    
    if ($optimizations.Count -eq 0) {
        Write-Host "  ✅ All servers optimized" -ForegroundColor Green
    } else {
        foreach ($opt in $optimizations) {
            Write-Host "  ⚡ $opt" -ForegroundColor Yellow
        }
    }
}

# Generate Health Score
$totalChecks = 20
$passedChecks = $totalChecks - $script:issues.Count - ($script:warnings.Count * 0.5)
$healthScore = [math]::Round(($passedChecks / $totalChecks) * 100, 1)

# Summary Report
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           Validation Summary              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n📊 Health Score: " -NoNewline
if ($healthScore -ge 90) {
    Write-Host "$healthScore%" -ForegroundColor Green -NoNewline
    Write-Host " 🏆 Excellent!"
} elseif ($healthScore -ge 70) {
    Write-Host "$healthScore%" -ForegroundColor Yellow -NoNewline
    Write-Host " ⚠️ Good, needs minor fixes"
} else {
    Write-Host "$healthScore%" -ForegroundColor Red -NoNewline
    Write-Host " ❌ Needs attention"
}

if ($script:issues.Count -gt 0) {
    Write-Host "`n❌ Critical Issues ($($script:issues.Count)):" -ForegroundColor Red
    $script:issues | ForEach-Object { Write-Host "   • $_" }
}

if ($script:warnings.Count -gt 0) {
    Write-Host "`n⚠️ Warnings ($($script:warnings.Count)):" -ForegroundColor Yellow
    $script:warnings | ForEach-Object { Write-Host "   • $_" }
}

if ($script:fixes.Count -gt 0) {
    Write-Host "`n✅ Auto-Fixed ($($script:fixes.Count)):" -ForegroundColor Green
    $script:fixes | ForEach-Object { Write-Host "   • $_" }
}

Write-Host "`n💡 Next Steps:" -ForegroundColor Cyan
if ($script:issues.Count -gt 0) {
    Write-Host "  1. Run with -AutoFix flag to attempt automatic fixes"
    Write-Host "  2. Check network/firewall settings for connectivity issues"
}
if ($accessibleAccounts -lt $profiles.Count) {
    Write-Host "  3. Run .\login-all-accounts.ps1 to access all AWS accounts"
}
Write-Host "  4. Run .\test-servers.ps1 for detailed server testing"

# Export report
$report = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    HealthScore = $healthScore
    Issues = $script:issues
    Warnings = $script:warnings
    Fixes = $script:fixes
    AccessibleAccounts = $accessibleAccounts
}

$reportPath = ".\logs\validation-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
New-Item -Path ".\logs" -ItemType Directory -Force | Out-Null
$report | ConvertTo-Json -Depth 5 | Set-Content $reportPath

Write-Host "`n📄 Full report saved to: $reportPath" -ForegroundColor Gray

# Return exit code based on health
if ($healthScore -lt 70) { exit 1 }
exit 0
