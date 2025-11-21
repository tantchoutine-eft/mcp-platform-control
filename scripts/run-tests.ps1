# MCP Automated Test Suite
# Comprehensive testing framework for all MCP components

param(
    [string]$TestSuite = "All",
    [switch]$Verbose,
    [switch]$ExportResults,
    [switch]$ContinueOnError
)

$ErrorActionPreference = if ($ContinueOnError) { "Continue" } else { "Stop" }

Write-Host "`n🧪 MCP Automated Test Suite" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "Test Suite: $TestSuite" -ForegroundColor Gray
Write-Host "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Test results storage
$script:testResults = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    Tests = @()
}

function Run-Test {
    param(
        [string]$Name,
        [string]$Category,
        [scriptblock]$Test,
        [string]$Description
    )
    
    if ($TestSuite -ne "All" -and $TestSuite -ne $Category) {
        $script:testResults.Skipped++
        return
    }
    
    Write-Host "`n📌 Testing: $Name" -ForegroundColor Yellow
    if ($Description) {
        Write-Host "   $Description" -ForegroundColor Gray
    }
    
    $testStart = Get-Date
    $result = @{
        Name = $Name
        Category = $Category
        StartTime = $testStart
    }
    
    try {
        $output = & $Test
        $result.Status = "Passed"
        $result.Output = $output
        $script:testResults.Passed++
        Write-Host "   ✅ PASSED" -ForegroundColor Green
        if ($Verbose -and $output) {
            Write-Host "   Output: $output" -ForegroundColor Gray
        }
    } catch {
        $result.Status = "Failed"
        $result.Error = $_.Exception.Message
        $script:testResults.Failed++
        Write-Host "   ❌ FAILED: $_" -ForegroundColor Red
    } finally {
        $result.Duration = ((Get-Date) - $testStart).TotalSeconds
        $script:testResults.Tests += $result
    }
}

# === CONFIGURATION TESTS ===
Write-Host "`n🔧 Configuration Tests" -ForegroundColor Cyan

Run-Test -Name "JSON Configuration Validity" -Category "Configuration" -Description "Validate all JSON configs" -Test {
    $configs = Get-ChildItem -Path ".\configs" -Filter "*.json" -Recurse
    foreach ($config in $configs) {
        $null = Get-Content $config.FullName -Raw | ConvertFrom-Json
    }
    return "$($configs.Count) configurations valid"
}

Run-Test -Name "Path Resolution" -Category "Configuration" -Description "Verify dynamic paths work" -Test {
    $uvPath = "$env:USERPROFILE\.local\bin\uvx.exe"
    if (-not (Test-Path $uvPath)) {
        throw "UV not found at expected path"
    }
    return "Paths resolved correctly"
}

Run-Test -Name "Template Integrity" -Category "Configuration" -Description "Verify templates are valid" -Test {
    $templates = Get-ChildItem -Path ".\templates" -Filter "*.json"
    foreach ($template in $templates) {
        $content = Get-Content $template.FullName -Raw | ConvertFrom-Json
        if (-not $content.PSObject.Properties.Name) {
            throw "Invalid template: $($template.Name)"
        }
    }
    return "$($templates.Count) templates valid"
}

# === AWS CONNECTIVITY TESTS ===
Write-Host "`n☁️ AWS Connectivity Tests" -ForegroundColor Cyan

Run-Test -Name "AWS CLI Installation" -Category "AWS" -Description "Check AWS CLI is available" -Test {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not installed"
    }
    return $awsVersion
}

Run-Test -Name "SSO Configuration" -Category "AWS" -Description "Verify SSO profiles exist" -Test {
    $profiles = @("aws-sso-primary", "aws-sso-sandbox", "aws-sso-nonprod", 
                  "aws-sso-prod", "aws-sso-security", "aws-sso-infrastructure", "aws-sso-logs")
    
    $configFile = "$env:USERPROFILE\.aws\config"
    if (-not (Test-Path $configFile)) {
        throw "AWS config file not found"
    }
    
    $configContent = Get-Content $configFile -Raw
    $missingProfiles = @()
    
    foreach ($profile in $profiles) {
        if ($configContent -notmatch "\[profile $profile\]") {
            $missingProfiles += $profile
        }
    }
    
    if ($missingProfiles.Count -gt 0) {
        throw "Missing profiles: $($missingProfiles -join ', ')"
    }
    
    return "All $($profiles.Count) profiles configured"
}

Run-Test -Name "Primary Account Access" -Category "AWS" -Description "Test primary account connectivity" -Test {
    $identity = aws sts get-caller-identity --profile aws-sso-primary 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot access primary account. Run: aws sso login --profile aws-sso-primary"
    }
    $id = $identity | ConvertFrom-Json
    return "Connected to account $($id.Account)"
}

# === MCP SERVER TESTS ===
Write-Host "`n🚀 MCP Server Tests" -ForegroundColor Cyan

Run-Test -Name "UV Installation" -Category "MCP" -Description "Verify UV package manager" -Test {
    $uvPath = "$env:USERPROFILE\.local\bin\uv.exe"
    if (-not (Test-Path $uvPath)) {
        throw "UV not installed"
    }
    $version = & $uvPath --version 2>&1
    return "UV $version installed"
}

Run-Test -Name "Python 3.13" -Category "MCP" -Description "Verify Python version" -Test {
    $uvPath = "$env:USERPROFILE\.local\bin\uv.exe"
    $pythonList = & $uvPath python list 2>&1
    if ($pythonList -notmatch "3\.13") {
        throw "Python 3.13 not installed"
    }
    return "Python 3.13 available"
}

$mcpServers = @(
    @{Name="AWS Core"; Package="awslabs.core-mcp-server@latest"},
    @{Name="AWS CDK"; Package="awslabs.cdk-mcp-server@latest"},
    @{Name="AWS Pricing"; Package="awslabs.aws-pricing-mcp-server@latest"},
    @{Name="AWS API"; Package="awslabs.aws-api-mcp-server@latest"}
)

foreach ($server in $mcpServers) {
    Run-Test -Name "$($server.Name) Package" -Category "MCP" -Description "Test $($server.Name) availability" -Test {
        $uvx = "$env:USERPROFILE\.local\bin\uvx.exe"
        $output = & $uvx $server.Package --help 2>&1 | Select-String "usage:"
        if (-not $output) {
            throw "Package not accessible"
        }
        return "Package ready"
    }
}

# === SCRIPT TESTS ===
Write-Host "`n📜 Script Tests" -ForegroundColor Cyan

$scripts = @(
    ".\scripts\install-prerequisites.ps1",
    ".\scripts\login-all-accounts.ps1",
    ".\scripts\test-servers.ps1",
    ".\scripts\update-aws-session.ps1",
    ".\scripts\validate-configuration.ps1",
    ".\scripts\generate-config.ps1",
    ".\scripts\security-audit.ps1",
    ".\scripts\performance-monitor.ps1"
)

foreach ($script in $scripts) {
    if (Test-Path $script) {
        Run-Test -Name "$(Split-Path $script -Leaf) Syntax" -Category "Scripts" -Description "Validate PowerShell syntax" -Test {
            $errors = @()
            $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $script -Raw), [ref]$errors)
            if ($errors.Count -gt 0) {
                throw "Syntax errors: $($errors[0].Message)"
            }
            return "Syntax valid"
        }
    }
}

# === SECURITY TESTS ===
Write-Host "`n🔒 Security Tests" -ForegroundColor Cyan

Run-Test -Name "No Hardcoded Secrets" -Category "Security" -Description "Check for exposed credentials" -Test {
    $patterns = @(
        'password\s*=\s*["\'][^"\']+["\']',
        'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        'secret\s*=\s*["\'][^"\']+["\']',
        'token\s*=\s*["\'][^"\']+["\']'
    )
    
    $files = Get-ChildItem -Path "." -Include "*.json", "*.ps1", "*.md" -Recurse -Exclude "test-*", "*.example.*"
    $issues = @()
    
    foreach ($file in $files) {
        $content = Get-Content $file.FullName -Raw
        foreach ($pattern in $patterns) {
            if ($content -match $pattern) {
                # Check if it's a placeholder
                if ($matches[0] -notmatch 'YOUR_|EXAMPLE|example|placeholder|\$\{') {
                    $issues += "$($file.Name): Potential secret exposed"
                }
            }
        }
    }
    
    if ($issues.Count -gt 0) {
        throw $issues -join "; "
    }
    return "No secrets exposed"
}

Run-Test -Name "File Permissions" -Category "Security" -Description "Check sensitive file permissions" -Test {
    $cursorConfig = "$env:USERPROFILE\.cursor\mcp.json"
    if (Test-Path $cursorConfig) {
        $acl = Get-Acl $cursorConfig
        $publicAccess = $acl.Access | Where-Object { $_.IdentityReference -like "*Everyone*" }
        if ($publicAccess) {
            throw "Config file has public access"
        }
    }
    return "Permissions secure"
}

# === PERFORMANCE TESTS ===
Write-Host "`n⚡ Performance Tests" -ForegroundColor Cyan

Run-Test -Name "Configuration Load Time" -Category "Performance" -Description "Measure config parsing speed" -Test {
    $configPath = ".\configs\mcp.json"
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $null = Get-Content $configPath -Raw | ConvertFrom-Json
    $stopwatch.Stop()
    
    if ($stopwatch.ElapsedMilliseconds -gt 1000) {
        throw "Config load too slow: $($stopwatch.ElapsedMilliseconds)ms"
    }
    return "Load time: $($stopwatch.ElapsedMilliseconds)ms"
}

Run-Test -Name "Script Execution Speed" -Category "Performance" -Description "Test script response times" -Test {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $null = & powershell -Command "exit 0"
    $stopwatch.Stop()
    
    if ($stopwatch.ElapsedMilliseconds -gt 3000) {
        throw "PowerShell startup slow: $($stopwatch.ElapsedMilliseconds)ms"
    }
    return "Startup time: $($stopwatch.ElapsedMilliseconds)ms"
}

# === INTEGRATION TESTS ===
Write-Host "`n🔗 Integration Tests" -ForegroundColor Cyan

Run-Test -Name "End-to-End Config Generation" -Category "Integration" -Description "Test complete config generation flow" -Test {
    $testOutput = ".\test-output\test-config.json"
    New-Item -Path ".\test-output" -ItemType Directory -Force | Out-Null
    
    # Run config generator
    $result = & powershell -Command ".\scripts\generate-config.ps1 -Output '$testOutput' -Profile 'aws-sso-primary' -Region 'us-east-1'" 2>&1
    
    if (-not (Test-Path $testOutput)) {
        throw "Config generation failed"
    }
    
    # Validate generated config
    $config = Get-Content $testOutput -Raw | ConvertFrom-Json
    if (-not $config.mcpServers) {
        throw "Invalid generated config"
    }
    
    # Cleanup
    Remove-Item $testOutput -Force
    Remove-Item ".\test-output" -Recurse -Force -ErrorAction SilentlyContinue
    
    return "Config generation successful"
}

# === GENERATE REPORT ===
Write-Host "`n📊 Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

$total = $script:testResults.Passed + $script:testResults.Failed + $script:testResults.Skipped
$passRate = if ($total -gt 0) { [math]::Round(($script:testResults.Passed / $total) * 100, 1) } else { 0 }

Write-Host "`n✅ Passed:  $($script:testResults.Passed)" -ForegroundColor Green
Write-Host "❌ Failed:  $($script:testResults.Failed)" -ForegroundColor $(if ($script:testResults.Failed -gt 0) { "Red" } else { "Gray" })
Write-Host "⏭️ Skipped: $($script:testResults.Skipped)" -ForegroundColor Gray
Write-Host "📈 Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 70) { "Yellow" } else { "Red" })

# Display failed tests
if ($script:testResults.Failed -gt 0) {
    Write-Host "`n❌ Failed Tests:" -ForegroundColor Red
    $script:testResults.Tests | Where-Object { $_.Status -eq "Failed" } | ForEach-Object {
        Write-Host "  • $($_.Name): $($_.Error)" -ForegroundColor Red
    }
}

# Export results
if ($ExportResults) {
    $exportData = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Suite = $TestSuite
        Summary = @{
            Total = $total
            Passed = $script:testResults.Passed
            Failed = $script:testResults.Failed
            Skipped = $script:testResults.Skipped
            PassRate = $passRate
        }
        Tests = $script:testResults.Tests
    }
    
    $exportPath = ".\logs\test-results-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    New-Item -Path ".\logs" -ItemType Directory -Force | Out-Null
    $exportData | ConvertTo-Json -Depth 5 | Set-Content $exportPath
    Write-Host "`n📄 Results exported to: $exportPath" -ForegroundColor Gray
}

# Exit code
if ($script:testResults.Failed -gt 0) {
    Write-Host "`n⚠️ Tests failed. Please review and fix issues." -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n✅ All tests passed successfully!" -ForegroundColor Green
    exit 0
}
