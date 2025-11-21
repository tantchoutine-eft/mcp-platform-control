# MCP Server Troubleshooting Guide

## 🔴 Common Issues and Solutions

### 1. Server Shows Red Error Indicator in Cursor

#### Issue: "uvx is not recognized as an internal or external command"
**Solution**:
```powershell
# Install UV package manager
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Add to PATH permanently
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Users\$env:USERNAME\.local\bin", [EnvironmentVariableTarget]::User)

# Restart Cursor IDE
```

#### Issue: "Combined server and tool name length exceeds 60 characters"
**Solution**: Already fixed by using shorter server names in configuration

#### Issue: Server package deprecated
**Solution**: Update to newer package name (e.g., `cost-analysis` → `aws-pricing`)

---

### 2. AWS Authentication Issues

#### Issue: "Token has expired and refresh failed"
**Solution**:
```powershell
# Re-login to AWS SSO
aws sso login --profile aws-sso-primary

# Verify authentication
aws sts get-caller-identity --profile aws-sso-primary
```

#### Issue: "Unable to locate credentials"
**Solution**:
```powershell
# Configure AWS SSO profile
aws configure sso

# Set profile name: aws-sso-primary
# SSO start URL: https://your-org.awsapps.com/start
# SSO region: us-east-1
# SSO account ID: Your account ID
# SSO role name: Your role
```

---

### 3. Python/Package Issues

#### Issue: "No module named 'awslabs'"
**Solution**:
```powershell
# Install Python 3.13
C:\Users\$env:USERNAME\.local\bin\uv.exe python install 3.13

# Test package installation
C:\Users\$env:USERNAME\.local\bin\uvx.exe awslabs.core-mcp-server@latest --help
```

#### Issue: Package installation fails
**Solution**:
```powershell
# Clear UV cache
Remove-Item -Path "$env:LOCALAPPDATA\uv\cache" -Recurse -Force

# Retry installation
C:\Users\$env:USERNAME\.local\bin\uvx.exe awslabs.core-mcp-server@latest --help
```

---

### 4. Database Connection Issues

#### Issue: MySQL server connection fails
**Possible Causes**:
1. **Network connectivity**: Ensure you can reach the RDS endpoint
2. **Security group**: Check port 3306 is open from your IP
3. **Secrets Manager**: Verify secret ARN is correct
4. **Database name**: Confirm database exists

**Diagnostic Steps**:
```powershell
# Test network connectivity
Test-NetConnection expanseft-prototype.c32erjvbancm.us-east-1.rds.amazonaws.com -Port 3306

# Verify secret exists
aws secretsmanager describe-secret --secret-id "arn:aws:secretsmanager:..." --profile aws-sso-primary

# Check RDS cluster status
aws rds describe-db-clusters --db-cluster-identifier expanseft-platform-prototype --profile aws-sso-primary
```

---

### 5. Performance Issues

#### Issue: Servers are slow to respond
**Solutions**:
1. **First run is always slower** - Packages need to download
2. **Reduce logging**: Set `FASTMCP_LOG_LEVEL` to `ERROR`
3. **Check network**: Ensure stable internet connection
4. **System resources**: Close unnecessary applications

---

## 🛠️ Diagnostic Commands

### Check UV Installation
```powershell
C:\Users\$env:USERNAME\.local\bin\uv.exe --version
```

### List Installed Python Versions
```powershell
C:\Users\$env:USERNAME\.local\bin\uv.exe python list
```

### Test Individual MCP Server
```powershell
# Replace with any server package
C:\Users\$env:USERNAME\.local\bin\uvx.exe awslabs.core-mcp-server@latest --help
```

### View Cursor MCP Logs
1. In Cursor: Settings → Tools & MCP
2. Click "Show Output" next to any server
3. Review error messages

### Check AWS Credentials
```powershell
aws sts get-caller-identity --profile aws-sso-primary
aws configure list --profile aws-sso-primary
```

---

## 📊 Server Status Indicators

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 🟢 Green | Server is running | None needed |
| 🔴 Red with "Error" | Server failed to start | Click "Show Output" for details |
| ⚪ Gray | Server is disabled | Enable in configuration |
| 🟡 Yellow | Server is starting | Wait for initialization |

---

## 🔄 Recovery Procedures

### Complete Reset
```powershell
# 1. Stop Cursor IDE

# 2. Clear UV cache
Remove-Item -Path "$env:LOCALAPPDATA\uv\cache" -Recurse -Force

# 3. Reinstall UV
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 4. Reinstall Python
C:\Users\$env:USERNAME\.local\bin\uv.exe python install 3.13

# 5. Copy fresh configuration
Copy-Item C:\Users\Tim\EFT_Dev_Projects\MCP\configs\mcp.json C:\Users\$env:USERNAME\.cursor\mcp.json

# 6. Restart Cursor
```

### Server-Specific Reset
```powershell
# Remove specific server from mcp.json
# Or set "disabled": true for the problematic server
# Restart Cursor
# Re-enable server after fixing issue
```

---

## 📞 Getting Help

### Resources
1. **AWS Labs MCP Issues**: https://github.com/awslabs/mcp/issues
2. **Cursor Forums**: https://forum.cursor.com
3. **AWS Support**: Via AWS Console

### Information to Provide
When seeking help, include:
1. Server error message (from "Show Output")
2. MCP configuration (without secrets)
3. UV version: `uv --version`
4. Python version: `uv python list`
5. AWS CLI version: `aws --version`
6. Operating system: Windows version

---

## 🚫 Security Considerations

### Never Share
- AWS credentials
- Secret ARNs content
- Database passwords
- API keys

### Safe to Share
- Error messages (review first)
- Configuration structure
- Server names
- Package versions

---

## 📈 Monitoring

### Regular Health Checks
Run weekly:
```powershell
.\scripts\test-servers.ps1
```

### AWS Session Management
Check before important work:
```powershell
.\scripts\update-aws-session.ps1
```

### Update Packages
Monthly updates recommended:
```powershell
# Packages auto-update when using @latest tag
# Just restart Cursor to get updates
```
