# AWS SSO Session Update Script
# Refreshes AWS SSO authentication for MCP servers

Write-Host "AWS SSO Session Manager" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

$profile = "aws-sso-primary"

# Check current session status
Write-Host "`nChecking current AWS session..." -ForegroundColor Yellow
$currentSession = aws sts get-caller-identity --profile $profile 2>&1

if ($LASTEXITCODE -eq 0) {
    $identity = $currentSession | ConvertFrom-Json
    Write-Host "✓ Current session is active" -ForegroundColor Green
    Write-Host "  Account: $($identity.Account)"
    Write-Host "  User: $($identity.UserId.Split(':')[1])"
    Write-Host "  ARN: $($identity.Arn)"
    
    Write-Host "`nDo you want to refresh the session? (Y/N): " -NoNewline -ForegroundColor Cyan
    $response = Read-Host
    
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "Session refresh cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Login to AWS SSO
Write-Host "`nLogging into AWS SSO..." -ForegroundColor Yellow
Write-Host "Profile: $profile" -ForegroundColor Gray

aws sso login --profile $profile

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Successfully logged into AWS SSO" -ForegroundColor Green
    
    # Verify the new session
    $newSession = aws sts get-caller-identity --profile $profile 2>&1
    if ($LASTEXITCODE -eq 0) {
        $newIdentity = $newSession | ConvertFrom-Json
        Write-Host "`nSession Details:" -ForegroundColor Cyan
        Write-Host "  Account: $($newIdentity.Account)"
        Write-Host "  User: $($newIdentity.UserId.Split(':')[1])"
        Write-Host "  ARN: $($newIdentity.Arn)"
        
        # Test with a simple AWS command
        Write-Host "`nTesting AWS access..." -ForegroundColor Yellow
        $s3Buckets = aws s3 ls --profile $profile 2>&1 | Select-Object -First 5
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ AWS access verified" -ForegroundColor Green
        }
    }
} else {
    Write-Host "✗ Failed to login to AWS SSO" -ForegroundColor Red
    Write-Host "Please check your SSO configuration and try again." -ForegroundColor Yellow
}

Write-Host "`n======================" -ForegroundColor Green
Write-Host "Session update complete!" -ForegroundColor Green
Write-Host "`nNote: MCP servers will use this session automatically." -ForegroundColor Gray
Write-Host "No need to restart Cursor unless servers were previously failing." -ForegroundColor Gray
