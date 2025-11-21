# Get temporary credentials for a specific AWS SSO profile
param(
    [Parameter(Mandatory=$true)]
    [string]$Profile
)

# Get temporary credentials
$creds = aws sts get-caller-identity --profile $Profile --query 'Account' --output text 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Unable to get credentials for profile $Profile" -ForegroundColor Red
    Write-Host "Please run: aws sso login --sso-session expanse-sso" -ForegroundColor Yellow
    exit 1
}

# Export the credentials as JSON
$credentials = aws configure export-credentials --profile $Profile --format process | ConvertFrom-Json

if ($null -eq $credentials) {
    Write-Host "Error: Unable to export credentials for profile $Profile" -ForegroundColor Red
    exit 1
}

# Output credentials in a format that can be used by MCP
@{
    AccessKeyId = $credentials.AccessKeyId
    SecretAccessKey = $credentials.SecretAccessKey
    SessionToken = $credentials.SessionToken
    Expiration = $credentials.Expiration
} | ConvertTo-Json
