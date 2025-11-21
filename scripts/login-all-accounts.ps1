# AWS SSO Multi-Account Login Script
# Logs into all configured AWS accounts

Write-Host "AWS SSO Multi-Account Login" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

$accounts = @(
    @{Profile="aws-sso-primary"; Name="Management"; AccountId="886089548523"},
    @{Profile="aws-sso-sandbox"; Name="Sandbox"; AccountId="537124940140"},
    @{Profile="aws-sso-nonprod"; Name="NonProd"; AccountId="381492229443"},
    @{Profile="aws-sso-prod"; Name="Production"; AccountId="654654560452"},
    @{Profile="aws-sso-security"; Name="Security"; AccountId="131087618144"},
    @{Profile="aws-sso-infrastructure"; Name="Infrastructure"; AccountId="211125547824"},
    @{Profile="aws-sso-logs"; Name="Logs"; AccountId="213611281426"}
)

Write-Host "`nLogging into AWS SSO..." -ForegroundColor Yellow
aws sso login --sso-session expanse-sso

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ SSO login successful" -ForegroundColor Green
    
    Write-Host "`nVerifying access to all accounts:" -ForegroundColor Yellow
    Write-Host "----------------------------------"
    
    $successCount = 0
    $failCount = 0
    
    foreach ($account in $accounts) {
        Write-Host "`n$($account.Name) Account ($($account.AccountId)):" -ForegroundColor Cyan
        
        $identity = aws sts get-caller-identity --profile $account.Profile 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $identityJson = $identity | ConvertFrom-Json
            Write-Host "  ✓ Access verified" -ForegroundColor Green
            Write-Host "  Role: " -NoNewline
            Write-Host "$($identityJson.Arn.Split('/')[-2])" -ForegroundColor Gray
            $successCount++
        } else {
            Write-Host "  ✗ Access failed" -ForegroundColor Red
            $failCount++
        }
    }
    
    Write-Host "`n===========================" -ForegroundColor Green
    Write-Host "Summary:" -ForegroundColor Yellow
    Write-Host "  Accessible accounts: $successCount" -ForegroundColor Green
    Write-Host "  Failed accounts: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Gray" })
    
} else {
    Write-Host "✗ SSO login failed" -ForegroundColor Red
}

Write-Host "`nTip: Use the multi-account configuration to access different accounts:" -ForegroundColor Cyan
Write-Host "  Copy-Item .\configs\mcp-multi-account.json C:\Users\`$env:USERNAME\.cursor\mcp.json"
