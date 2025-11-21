# Multi-Account Access Fix

## The Problem
MCP servers don't properly isolate AWS profiles when multiple instances are running. All aws-api servers end up using the same profile (usually the primary one), regardless of the AWS_PROFILE environment variable setting.

## The Solution: Use Profile Switching in Commands

Instead of multiple aws-api servers, use ONE server and specify the profile in your commands.

### ✅ Working Approach

Use a single `aws-api` server and include `--profile` in your commands:

```
"Run aws s3 ls --profile aws-sso-sandbox"
"Execute aws ec2 describe-instances --profile aws-sso-prod --region us-east-1"
"Show aws rds describe-db-clusters --profile aws-sso-infrastructure"
```

### 📝 Quick Reference for Your Accounts

| Account | Profile to Use | Account ID |
|---------|---------------|------------|
| Management | `--profile aws-sso-primary` | 886089548523 |
| Sandbox | `--profile aws-sso-sandbox` | 537124940140 |
| NonProd | `--profile aws-sso-nonprod` | 381492229443 |
| Production | `--profile aws-sso-prod` | 654654560452 |
| Security | `--profile aws-sso-security` | 131087618144 |
| Infrastructure | `--profile aws-sso-infrastructure` | 211125547824 |
| Logs | `--profile aws-sso-logs` | 213611281426 |

### 💡 Example Commands

**Sandbox Account:**
```
"Using aws-api, run: aws s3 ls --profile aws-sso-sandbox"
"Execute: aws ec2 describe-instances --profile aws-sso-sandbox --query 'Reservations[].Instances[].InstanceId'"
```

**Production Account:**
```
"Run: aws rds describe-db-instances --profile aws-sso-prod"
"Execute: aws lambda list-functions --profile aws-sso-prod --region us-east-1"
```

**Infrastructure Account:**
```
"Show: aws vpc describe-vpcs --profile aws-sso-infrastructure"
"List: aws ecs list-clusters --profile aws-sso-infrastructure"
```

### 🔧 Apply the Fix

```powershell
# Use the single API configuration
Copy-Item C:\Users\Tim\EFT_Dev_Projects\MCP\configs\mcp-single-api.json C:\Users\$env:USERNAME\.cursor\mcp.json

# Restart Cursor
```

## Why This Happens

The AWS MCP server uses boto3 internally, which follows the AWS credential chain:
1. Environment variables (AWS_ACCESS_KEY_ID, etc.)
2. Shared credentials file
3. AWS config file
4. Instance metadata

When multiple MCP server processes start, they may share the same credential resolution context, causing all servers to use the same profile.

## Alternative Solutions (If Needed)

### Option 1: Use Assume Role
Instead of SSO profiles, use role assumption in commands:
```
"Assume role arn:aws:iam::537124940140:role/AdminRole then list S3 buckets"
```

### Option 2: Direct Credential Management
Use `aws sts get-session-token` to get temporary credentials for each account.

### Option 3: Wait for MCP Server Update
The AWS Labs team may fix this in future versions of the MCP servers.

## Verification

To verify which account you're accessing:
```
"Run: aws sts get-caller-identity --profile aws-sso-sandbox"
```

This will show the account number and confirm you're in the right account.
