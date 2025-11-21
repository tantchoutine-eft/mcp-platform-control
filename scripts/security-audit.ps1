# MCP Security Audit Script
# Comprehensive security analysis and recommendations

param(
    [switch]$Remediate,
    [switch]$Strict
)

Write-Host "`n🔒 MCP Security Audit Tool" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

$script:securityScore = 100
$script:findings = @()
$script:remediations = @()

function Test-SecurityControl {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [scriptblock]$Remediation,
        [int]$Severity = 5,  # 1-10 scale
        [string]$Description
    )
    
    Write-Host "`nChecking: $Name" -NoNewline
    try {
        $result = & $Test
        if ($result.Passed) {
            Write-Host " ✅ Passed" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ⚠️ Failed (Severity: $Severity/10)" -ForegroundColor Yellow
            $script:securityScore -= ($Severity * 2)
            $script:findings += @{
                Control = $Name
                Severity = $Severity
                Description = $Description
                Finding = $result.Message
            }
            
            if ($Remediate -and $Remediation) {
                Write-Host "  🔧 Applying remediation..." -ForegroundColor Cyan
                try {
                    & $Remediation
                    $script:remediations += "$Name remediated successfully"
                    Write-Host "  ✅ Remediated!" -ForegroundColor Green
                    $script:securityScore += $Severity  # Partial recovery
                } catch {
                    Write-Host "  ❌ Remediation failed: $_" -ForegroundColor Red
                }
            }
        }
    } catch {
        Write-Host " ❌ Error: $_" -ForegroundColor Red
        return $false
    }
}

# 1. Check for hardcoded credentials
Test-SecurityControl -Name "No Hardcoded Credentials" -Severity 10 -Description "Ensure no plaintext credentials in configurations" -Test {
    $configFiles = Get-ChildItem -Path ".\configs" -Filter "*.json" -Recurse
    $hardcodedFound = $false
    $findings = @()
    
    foreach ($file in $configFiles) {
        $content = Get-Content $file.FullName -Raw
        if ($content -match '"password":|"secret":|"api[_-]?key":|"access[_-]?key":|"private[_-]?key":') {
            $hardcodedFound = $true
            $findings += $file.Name
        }
    }
    
    return @{
        Passed = -not $hardcodedFound
        Message = if ($hardcodedFound) { "Potential credentials in: $($findings -join ', ')" } else { "No hardcoded credentials found" }
    }
}

# 2. AWS Credential Security
Test-SecurityControl -Name "AWS Credential Security" -Severity 8 -Description "AWS credentials should use SSO or temporary credentials" -Test {
    $awsConfig = "$env:USERPROFILE\.aws\credentials"
    if (Test-Path $awsConfig) {
        $content = Get-Content $awsConfig -Raw
        if ($content -match "aws_access_key_id|aws_secret_access_key" -and $content -notmatch "#.*aws_access_key_id") {
            return @{
                Passed = $false
                Message = "Long-term AWS credentials detected. Use SSO or temporary credentials instead."
            }
        }
    }
    
    return @{
        Passed = $true
        Message = "Using SSO or temporary credentials"
    }
}

# 3. File Permissions
Test-SecurityControl -Name "Configuration File Permissions" -Severity 6 -Description "Sensitive files should have restricted permissions" -Test {
    $sensitiveFiles = @(
        "$env:USERPROFILE\.cursor\mcp.json",
        "$env:USERPROFILE\.aws\config",
        "$env:USERPROFILE\.aws\credentials"
    )
    
    $issues = @()
    foreach ($file in $sensitiveFiles) {
        if (Test-Path $file) {
            $acl = Get-Acl $file
            $otherUsers = $acl.Access | Where-Object { 
                $_.IdentityReference -notlike "*$env:USERNAME*" -and 
                $_.IdentityReference -notlike "*SYSTEM*" -and
                $_.IdentityReference -notlike "*Administrators*"
            }
            if ($otherUsers) {
                $issues += Split-Path $file -Leaf
            }
        }
    }
    
    return @{
        Passed = $issues.Count -eq 0
        Message = if ($issues.Count -gt 0) { "Excessive permissions on: $($issues -join ', ')" } else { "File permissions are secure" }
    }
} -Remediation {
    $files = @("$env:USERPROFILE\.cursor\mcp.json", "$env:USERPROFILE\.aws\config", "$env:USERPROFILE\.aws\credentials")
    foreach ($file in $files) {
        if (Test-Path $file) {
            $acl = Get-Acl $file
            $acl.SetAccessRuleProtection($true, $false)
            $permission = "$env:USERNAME", "FullControl", "Allow"
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($accessRule)
            Set-Acl $file $acl
        }
    }
}

# 4. Network Security
Test-SecurityControl -Name "Network Encryption" -Severity 7 -Description "All connections should use TLS/SSL" -Test {
    $config = Get-Content "$env:USERPROFILE\.cursor\mcp.json" -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $insecureEndpoints = @()
    
    if ($config) {
        foreach ($server in $config.mcpServers.PSObject.Properties) {
            if ($server.Value.args -join " " -match "http://") {
                $insecureEndpoints += $server.Name
            }
        }
    }
    
    return @{
        Passed = $insecureEndpoints.Count -eq 0
        Message = if ($insecureEndpoints.Count -gt 0) { "Insecure HTTP in: $($insecureEndpoints -join ', ')" } else { "All connections use secure protocols" }
    }
}

# 5. Secret Rotation
Test-SecurityControl -Name "Secret Rotation Policy" -Severity 5 -Description "Secrets should be rotated regularly" -Test {
    # Check AWS SSO session age
    $ssoCache = Get-ChildItem "$env:USERPROFILE\.aws\sso\cache" -Filter "*.json" -ErrorAction SilentlyContinue | 
                Sort-Object LastWriteTime -Descending | 
                Select-Object -First 1
    
    if ($ssoCache) {
        $age = (Get-Date) - $ssoCache.LastWriteTime
        if ($age.Days -gt 30) {
            return @{
                Passed = $false
                Message = "SSO credentials are $($age.Days) days old. Rotate credentials regularly."
            }
        }
    }
    
    return @{
        Passed = $true
        Message = "Credentials are current"
    }
}

# 6. Audit Logging
Test-SecurityControl -Name "Audit Logging" -Severity 4 -Description "Audit logs should be enabled" -Test {
    $logDir = ".\logs"
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        return @{
            Passed = $false
            Message = "Audit log directory created"
        }
    }
    
    return @{
        Passed = $true
        Message = "Audit logging directory exists"
    }
}

# 7. Principle of Least Privilege
Test-SecurityControl -Name "Least Privilege" -Severity 6 -Description "Use read-only access where possible" -Test {
    $config = Get-Content "$env:USERPROFILE\.cursor\mcp.json" -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $recommendations = @()
    
    if ($config.mcpServers.'mysql-aurora'.args -notcontains "--readonly") {
        $recommendations += "MySQL Aurora should use read-only mode"
    }
    
    return @{
        Passed = $recommendations.Count -eq 0
        Message = if ($recommendations.Count -gt 0) { $recommendations -join "; " } else { "Least privilege implemented" }
    }
}

# 8. Multi-Factor Authentication
if ($Strict) {
    Test-SecurityControl -Name "Multi-Factor Authentication" -Severity 9 -Description "MFA should be enforced" -Test {
        # Check if AWS SSO is configured with MFA
        $identity = aws sts get-caller-identity --profile aws-sso-primary 2>&1
        if ($LASTEXITCODE -eq 0) {
            $identityJson = $identity | ConvertFrom-Json
            if ($identityJson.Arn -match "assumed-role.*mfa") {
                return @{ Passed = $true; Message = "MFA is active" }
            }
        }
        
        return @{
            Passed = $false
            Message = "MFA not detected or not enforced"
        }
    }
}

# Calculate final score
$script:securityScore = [Math]::Max(0, $script:securityScore)

# Generate Report
Write-Host "`n╔════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Security Audit Report        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n🛡️ Security Score: " -NoNewline
if ($script:securityScore -ge 90) {
    Write-Host "$script:securityScore/100" -ForegroundColor Green -NoNewline
    Write-Host " - Excellent Security Posture 🏆"
} elseif ($script:securityScore -ge 70) {
    Write-Host "$script:securityScore/100" -ForegroundColor Yellow -NoNewline
    Write-Host " - Good, Minor Improvements Needed"
} else {
    Write-Host "$script:securityScore/100" -ForegroundColor Red -NoNewline
    Write-Host " - Critical Security Issues Found!"
}

# Display findings
if ($script:findings.Count -gt 0) {
    Write-Host "`n⚠️ Security Findings:" -ForegroundColor Yellow
    $script:findings | Sort-Object -Property Severity -Descending | ForEach-Object {
        $severityColor = if ($_.Severity -ge 8) { "Red" } elseif ($_.Severity -ge 5) { "Yellow" } else { "Gray" }
        Write-Host "`n  [$($_.Severity)/10] $($_.Control)" -ForegroundColor $severityColor
        Write-Host "  └─ $($_.Finding)" -ForegroundColor Gray
    }
}

# Display remediations
if ($script:remediations.Count -gt 0) {
    Write-Host "`n✅ Applied Remediations:" -ForegroundColor Green
    $script:remediations | ForEach-Object { Write-Host "  • $_" }
}

# Recommendations
Write-Host "`n📋 Security Recommendations:" -ForegroundColor Cyan
$recommendations = @(
    "1. Enable AWS CloudTrail for audit logging",
    "2. Use AWS Secrets Manager for all sensitive data",
    "3. Implement regular credential rotation (30-90 days)",
    "4. Enable MFA on all AWS accounts",
    "5. Use temporary credentials via AWS SSO",
    "6. Regular security audits (monthly)",
    "7. Implement network segmentation for production access"
)

if ($script:securityScore -lt 90) {
    $recommendations | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "  ✅ Maintain current security practices" -ForegroundColor Green
    Write-Host "  📅 Schedule next audit in 30 days" -ForegroundColor Gray
}

# Export detailed report
$report = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    SecurityScore = $script:securityScore
    Findings = $script:findings
    Remediations = $script:remediations
    StrictMode = $Strict.IsPresent
}

$reportPath = ".\logs\security-audit-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
New-Item -Path ".\logs" -ItemType Directory -Force | Out-Null
$report | ConvertTo-Json -Depth 5 | Set-Content $reportPath

Write-Host "`n📄 Detailed report saved to: $reportPath" -ForegroundColor Gray

# Return exit code based on score
if ($script:securityScore -lt 70) { 
    Write-Host "`n⚠️ CRITICAL: Security score below acceptable threshold!" -ForegroundColor Red
    exit 1 
}
exit 0
