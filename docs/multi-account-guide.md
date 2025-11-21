# Multi-Account MCP Configuration Guide

## 📊 Your AWS Organization Structure

```
aws-primary-eft (Management) - 886089548523
├── Infrastructure - 211125547824
├── Sandbox - 537124940140
├── Security - 131087618144
├── Logs - 213611281426
├── NonProd - 381492229443
└── Production - 654654560452
```

## 🎯 Access Strategies

### Strategy 1: Multiple API Servers (Recommended)
Use the `mcp-multi-account.json` configuration which provides separate servers for each account:

```
aws-api-primary     → Management Account (886089548523)
aws-api-sandbox     → Sandbox Account (537124940140)
aws-api-nonprod     → NonProd Account (381492229443)
aws-api-prod        → Production Account (654654560452)
aws-api-security    → Security Account (131087618144)
aws-api-infrastructure → Infrastructure Account (211125547824)
aws-api-logs        → Logs Account (213611281426)
```

**Usage Examples**:
- "Using aws-api-sandbox, create an S3 bucket for testing"
- "With aws-api-prod server, list all running EC2 instances"
- "Through aws-api-security, show CloudTrail events"

### Strategy 2: Single API Server with Profile Switching
Keep one `aws-api` server and specify the profile in your commands:

**Usage Examples**:
- "List EC2 instances in account 537124940140 using profile aws-sso-sandbox"
- "Show S3 buckets in production account with profile aws-sso-prod"
- "Get IAM roles from security account using aws-sso-security profile"

### Strategy 3: Environment-Specific Configurations
Create separate configuration files for different environments:

- `mcp-dev.json` - Points to sandbox/nonprod
- `mcp-prod.json` - Points to production
- `mcp-security.json` - Points to security/logs

## 🔧 Implementation

### Enable Multi-Account Configuration
```powershell
# Use the multi-account configuration
Copy-Item C:\Users\Tim\EFT_Dev_Projects\MCP\configs\mcp-multi-account.json C:\Users\$env:USERNAME\.cursor\mcp.json

# Restart Cursor IDE
```

### Login to All Accounts
```powershell
# Login once to access all accounts
.\scripts\login-all-accounts.ps1
```

## 📝 Account-Specific Use Cases

### Management Account (886089548523)
**Profile**: `aws-sso-primary`
- Organization management
- Billing and cost management
- Account creation and management
- AWS Control Tower operations

### Sandbox Account (537124940140)
**Profile**: `aws-sso-sandbox`
- Development experiments
- POCs and testing
- Learning new services
- Non-critical workloads

### NonProd Account (381492229443)
**Profile**: `aws-sso-nonprod`
- Staging environments
- Integration testing
- Pre-production validation
- Performance testing

### Production Account (654654560452)
**Profile**: `aws-sso-prod`
- Live applications
- Customer-facing services
- Production databases
- Critical workloads

### Security Account (131087618144)
**Profile**: `aws-sso-security`
- Security tools and monitoring
- GuardDuty findings
- Security Hub aggregation
- IAM Access Analyzer

### Infrastructure Account (211125547824)
**Profile**: `aws-sso-infrastructure`
- Shared infrastructure
- Networking components
- CI/CD pipelines
- Shared services

### Logs Account (213611281426)
**Profile**: `aws-sso-logs`
- Centralized logging
- CloudTrail logs aggregation
- Log analytics
- Compliance audit logs

## 🔒 Security Best Practices

### 1. Account Isolation
- Use separate MCP servers for production
- Never mix dev and prod operations
- Be explicit about target account

### 2. Least Privilege
- Consider creating read-only roles for some MCP servers
- Limit production access to specific operations
- Use separate profiles for different permission levels

### 3. Audit Trail
- All MCP operations are logged via CloudTrail
- Monitor cross-account access
- Review unexpected account access

## 💡 Pro Tips

### 1. Naming Convention in Prompts
Always specify the account when giving commands:
- ❌ "List EC2 instances"
- ✅ "List EC2 instances in sandbox account"
- ✅ "Using aws-api-prod, show RDS clusters"

### 2. Account Verification
Before critical operations:
```
"What account am I currently using?"
"Show the current AWS identity"
```

### 3. Batch Operations Across Accounts
```
"Compare EC2 instances between sandbox and production"
"List S3 buckets in all accounts"
```

### 4. Use Account Aliases
Instead of memorizing account IDs:
- Sandbox = 537124940140
- Prod = 654654560452
- Security = 131087618144

## 🚨 Common Pitfalls

### Wrong Account Operations
**Problem**: Running dev commands in production
**Solution**: Always verify account before operations

### Session Expiry
**Problem**: SSO session expires during work
**Solution**: Run `.\scripts\login-all-accounts.ps1` to refresh

### Cross-Account Resource Access
**Problem**: Trying to access resources in different account
**Solution**: Use the correct account-specific MCP server

## 📊 Quick Reference

| Account | ID | Profile | MCP Server |
|---------|-----|---------|------------|
| Management | 886089548523 | aws-sso-primary | aws-api-primary |
| Sandbox | 537124940140 | aws-sso-sandbox | aws-api-sandbox |
| NonProd | 381492229443 | aws-sso-nonprod | aws-api-nonprod |
| Production | 654654560452 | aws-sso-prod | aws-api-prod |
| Security | 131087618144 | aws-sso-security | aws-api-security |
| Infrastructure | 211125547824 | aws-sso-infrastructure | aws-api-infrastructure |
| Logs | 213611281426 | aws-sso-logs | aws-api-logs |

## 🔄 Switching Between Configurations

### For Development Work
```powershell
Copy-Item .\configs\mcp.json C:\Users\$env:USERNAME\.cursor\mcp.json
```

### For Multi-Account Work
```powershell
Copy-Item .\configs\mcp-multi-account.json C:\Users\$env:USERNAME\.cursor\mcp.json
```

Remember to restart Cursor after switching configurations!
