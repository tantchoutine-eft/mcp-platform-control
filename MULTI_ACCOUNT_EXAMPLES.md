# Multi-Account Command Examples

## 🎯 The Fix: Use `--profile` in Every Command

Since multiple MCP server instances don't isolate AWS profiles properly, we use ONE `aws-api` server and specify the profile in each command.

## 📝 Copy-Paste Examples for Each Account

### Management Account (886089548523)
```
aws s3 ls --profile aws-sso-primary
aws ec2 describe-instances --profile aws-sso-primary
aws iam list-users --profile aws-sso-primary
```

### Sandbox Account (537124940140)
```
aws s3 ls --profile aws-sso-sandbox
aws ec2 describe-instances --profile aws-sso-sandbox --query "Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key=='Name'].Value|[0]]" --output table
aws lambda list-functions --profile aws-sso-sandbox
```

### NonProd Account (381492229443)
```
aws rds describe-db-instances --profile aws-sso-nonprod
aws ecs list-clusters --profile aws-sso-nonprod
aws dynamodb list-tables --profile aws-sso-nonprod
```

### Production Account (654654560452)
```
aws s3 ls --profile aws-sso-prod
aws ec2 describe-instances --profile aws-sso-prod --filters "Name=instance-state-name,Values=running"
aws cloudwatch describe-alarms --profile aws-sso-prod --state-value ALARM
```

### Security Account (131087618144)
```
aws guardduty list-detectors --profile aws-sso-security
aws securityhub get-findings --profile aws-sso-security --max-items 10
aws cloudtrail lookup-events --profile aws-sso-security --max-items 10
```

### Infrastructure Account (211125547824)
```
aws ec2 describe-vpcs --profile aws-sso-infrastructure
aws ec2 describe-transit-gateways --profile aws-sso-infrastructure
aws route53 list-hosted-zones --profile aws-sso-infrastructure
```

### Logs Account (213611281426)
```
aws logs describe-log-groups --profile aws-sso-logs
aws s3 ls --profile aws-sso-logs
aws cloudtrail describe-trails --profile aws-sso-logs
```

## 💡 Pro Tips

### 1. Always Verify Account First
Before running critical commands:
```
aws sts get-caller-identity --profile aws-sso-prod
```

### 2. Cross-Account Comparison
Ask the aws-api server:
```
"Compare by running:
1. aws s3 ls --profile aws-sso-sandbox
2. aws s3 ls --profile aws-sso-prod
Show me the differences"
```

### 3. Use Aliases in Your Prompts
Instead of typing the full profile name, tell the AI:
```
"In sandbox (use aws-sso-sandbox profile), create an S3 bucket named test-mcp-demo"
"In production (use aws-sso-prod profile), list all RDS instances"
```

### 4. Batch Commands
```
"Run these commands:
- aws ec2 describe-instances --profile aws-sso-sandbox --query 'Reservations[].Instances[].[InstanceId]' --output text
- aws ec2 describe-instances --profile aws-sso-nonprod --query 'Reservations[].Instances[].[InstanceId]' --output text
- aws ec2 describe-instances --profile aws-sso-prod --query 'Reservations[].Instances[].[InstanceId]' --output text
Compare the instance counts"
```

## 🔄 Quick Account Switch Pattern

When working with multiple accounts, use this pattern:
```
"Check current identity: aws sts get-caller-identity --profile [PROFILE]"
"List resources: aws [SERVICE] [COMMAND] --profile [PROFILE]"
"Verify results: aws [SERVICE] describe-[RESOURCE] --profile [PROFILE]"
```

## ⚡ Speed Tips

### Create Shortcuts in Your Prompts
Tell the AI once at the beginning:
```
"For this session:
- 'sandbox' means use --profile aws-sso-sandbox
- 'prod' means use --profile aws-sso-prod
- 'infra' means use --profile aws-sso-infrastructure"
```

Then use:
```
"In sandbox, list S3 buckets"
"In prod, show running EC2 instances"
"In infra, describe VPCs"
```

## 🎯 Remember

**ALWAYS include `--profile` in your AWS commands when using the aws-api MCP server!**

Without it, commands default to the primary account (886089548523).
