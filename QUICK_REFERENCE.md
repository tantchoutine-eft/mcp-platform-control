# MCP Quick Reference

## 🚀 Quick Commands

### First Time Setup
```powershell
cd C:\Users\Tim\EFT_Dev_Projects\MCP
.\scripts\install-prerequisites.ps1
Copy-Item .\configs\mcp.json C:\Users\$env:USERNAME\.cursor\mcp.json
aws sso login --profile aws-sso-primary
# Restart Cursor IDE
```

### Daily Use
```powershell
# Update AWS session (if expired)
.\scripts\update-aws-session.ps1

# Test servers
.\scripts\test-servers.ps1
```

## 💬 Example Prompts by Server

### AWS Core (`aws-core`)
- "Design a serverless architecture for real-time analytics"
- "What's the best way to implement a data lake on AWS?"

### AWS CDK (`aws-cdk`)
- "Create CDK code for a three-tier web application"
- "Generate a Lambda function with DynamoDB table"

### AWS Pricing (`aws-pricing`)
- "Compare costs of t3.large vs t3.xlarge in us-east-1"
- "What's the monthly cost for 1TB of S3 storage?"

### AWS API (`aws-api`)
- "List all running EC2 instances"
- "Show me my RDS clusters"
- "Get all S3 buckets created this month"

### MySQL Aurora (`mysql-aurora`)
- "Show all tables in the database"
- "Find transactions from last week"
- "What's the schema of the users table?"

### Bedrock KB (`bedrock-kb`)
- "Search documentation for API endpoints"
- "Find information about authentication"

### Nova Canvas (`nova-canvas`)
- "Generate a modern dashboard UI"
- "Create an architecture diagram"

## 🔑 Key Paths

| Item | Path |
|------|------|
| MCP Config | `C:\Users\Tim\.cursor\mcp.json` |
| Project Root | `C:\Users\Tim\EFT_Dev_Projects\MCP` |
| UV Binary | `C:\Users\Tim\.local\bin\uvx.exe` |
| Scripts | `C:\Users\Tim\EFT_Dev_Projects\MCP\scripts` |

## 🎯 Keyboard Shortcuts in Cursor

| Action | Shortcut |
|--------|----------|
| Open MCP Settings | `Ctrl+,` → Tools & MCP |
| New Chat | `Ctrl+L` |
| Toggle AI Panel | `Ctrl+Shift+L` |

## 🔧 Common Fixes

### Server showing red error
```powershell
# Click "Show Output" to see error
# Usually: Restart Cursor or update AWS session
```

### AWS session expired
```powershell
aws sso login --profile aws-sso-primary
```

### UV not found
```powershell
$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
```

## 📊 Server Status Check

```powershell
# Quick status check
Get-Content C:\Users\$env:USERNAME\.cursor\mcp.json | Select-String '"disabled":'

# Full test
.\scripts\test-servers.ps1
```

## 🔄 Update Configuration

```powershell
# After editing configs\mcp.json
Copy-Item .\configs\mcp.json C:\Users\$env:USERNAME\.cursor\mcp.json
# Restart Cursor
```

## 💡 Pro Tips

1. **Batch Operations**: Ask multiple related questions in one prompt
2. **Context Matters**: Provide context about your project for better suggestions
3. **Combine Servers**: "Use CDK to create infrastructure then estimate costs"
4. **Save Examples**: Keep successful prompts in a notes file
5. **Check Output**: Always review generated code before using

## 📝 Notes Section
<!-- Add your own notes and frequently used commands here -->


---
_Last Updated: November 2025_
