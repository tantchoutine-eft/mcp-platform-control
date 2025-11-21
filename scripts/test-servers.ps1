# MCP Server Testing Script
# Tests each MCP server to ensure it's working properly

Write-Host "MCP Server Testing Utility" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

$uvPath = "C:\Users\$env:USERNAME\.local\bin\uvx.exe"

if (-not (Test-Path $uvPath)) {
    Write-Host "Error: UV not found at $uvPath" -ForegroundColor Red
    Write-Host "Please run install-prerequisites.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Server configurations
$servers = @(
    @{
        Name = "AWS Core"
        Package = "awslabs.core-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "AWS CDK"
        Package = "awslabs.cdk-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "AWS Pricing"
        Package = "awslabs.aws-pricing-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "AWS API"
        Package = "awslabs.aws-api-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "Bedrock KB"
        Package = "awslabs.bedrock-kb-retrieval-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "Nova Canvas"
        Package = "awslabs.nova-canvas-mcp-server@latest"
        TestCommand = "--help"
    },
    @{
        Name = "MySQL Aurora"
        Package = "awslabs.mysql-mcp-server@latest"
        TestCommand = "--help"
    }
)

Write-Host "`nTesting MCP Servers:" -ForegroundColor Yellow
Write-Host "--------------------"

$successCount = 0
$failureCount = 0

foreach ($server in $servers) {
    Write-Host "`nTesting: $($server.Name)" -ForegroundColor Cyan
    Write-Host "Package: $($server.Package)"
    
    try {
        $output = & $uvPath $server.Package $server.TestCommand 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "✓ Server is accessible and working" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Server returned error code: $exitCode" -ForegroundColor Red
            $failureCount++
        }
    } catch {
        Write-Host "✗ Failed to test server: $_" -ForegroundColor Red
        $failureCount++
    }
}

Write-Host "`n==========================" -ForegroundColor Green
Write-Host "Test Results:" -ForegroundColor Yellow
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failureCount" -ForegroundColor $(if ($failureCount -gt 0) { "Red" } else { "Gray" })

# Check AWS credentials
Write-Host "`nChecking AWS Credentials:" -ForegroundColor Yellow
Write-Host "-------------------------"

try {
    $awsIdentity = aws sts get-caller-identity --profile aws-sso-primary 2>&1
    if ($LASTEXITCODE -eq 0) {
        $identity = $awsIdentity | ConvertFrom-Json
        Write-Host "✓ AWS SSO is active" -ForegroundColor Green
        Write-Host "  Account: $($identity.Account)"
        Write-Host "  User: $($identity.UserId.Split(':')[1])"
    } else {
        Write-Host "⚠ AWS SSO session expired or not configured" -ForegroundColor Yellow
        Write-Host "  Run: aws sso login --profile aws-sso-primary"
    }
} catch {
    Write-Host "✗ Failed to check AWS credentials: $_" -ForegroundColor Red
}

Write-Host "`nTest complete!" -ForegroundColor Green
