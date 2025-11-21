# Platform Control Plane - Unified Multi-Cloud & Vendor MCP

A single natural language control plane for AWS, Azure, GCP, SentinelOne, Cisco, and any other infrastructure provider - all through one MCP server in Cursor.

## 🎯 Architecture Philosophy

**One MCP. Many Providers. Simple Commands.**

Instead of:
- "Use aws-api server to scale the ASG galileo-notify-asg in us-east-1"
- "Use azure-api to check VMSS status"
- "Use sentinelone-api to isolate endpoint"

You say:
- "Scale Galileo Notifications in prod to 4 instances"
- "Show VPN status for main datacenter link"
- "Isolate the compromised SQL server"

## 🏗️ Architecture

```
┌─────────────────┐
│   Cursor IDE    │
│   Natural       │
│   Language      │
└────────┬────────┘
         │
    ┌────▼────┐
    │   MCP   │
    │ Platform│
    │   Hub   │
    └────┬────┘
         │
    ┌────▼─────────────────────────────┐
    │  Canonical Resource Abstraction  │
    │  (domains.yml + providers.yml)   │
    └────┬─────────────────────────────┘
         │
    ┌────▼────┬──────┬──────┬──────┬──────┐
    │  AWS    │Azure │ GCP  │Sentinel│Cisco│
    │Provider │      │      │  One   │     │
    └─────────┴──────┴──────┴────────┴──────┘
```

## 📁 Project Structure

```
platform-control-plane/
├── mcp_server/
│   ├── main.py                 # MCP entry point
│   ├── tools/
│   │   ├── infrastructure.py   # restart/scale/deploy/status
│   │   ├── security.py        # alerts/isolate/compliance
│   │   ├── networking.py      # vpn/firewall/connectivity
│   │   └── observability.py   # logs/metrics/traces
│   ├── providers/
│   │   ├── base.py           # Abstract interfaces
│   │   ├── aws_provider.py
│   │   ├── azure_provider.py
│   │   ├── gcp_provider.py
│   │   ├── sentinelone_provider.py
│   │   └── cisco_provider.py
│   ├── core/
│   │   ├── resolver.py       # Domain → Provider resolution
│   │   ├── guardrails.py     # Safety checks & confirmations
│   │   └── audit.py          # Operation logging
│   └── utils/
│       ├── credentials.py
│       └── config.py
├── config/
│   ├── domains.yml           # Service → Provider mapping
│   ├── providers.yml         # Provider configurations
│   ├── policies.yml          # Guardrails & permissions
│   └── environments.yml      # Environment definitions
├── tests/
└── docs/
```

## 🔧 Configuration

### domains.yml
Maps logical services to actual resources:
```yaml
galileo_notifications:
  prod:
    compute:
      provider: aws
      kind: asg
      ref: galileo-notify-asg-prod
      region: us-east-1
    database:
      provider: aws
      kind: rds
      ref: galileo-db-prod-cluster
  staging:
    compute:
      provider: azure
      kind: vmss
      ref: galileo-notify-vmss-stg
      resource_group: expanseft-staging
```

### providers.yml
Provider-specific configurations:
```yaml
aws:
  accounts:
    prod: "654654560452"
    staging: "381492229443"
  default_region: us-east-1
  
azure:
  subscriptions:
    prod: "prod-subscription-id"
    staging: "staging-subscription-id"
  default_location: eastus

sentinelone:
  account_id: "your-account"
  site_ids:
    prod: "prod-site-id"
    corp: "corp-site-id"
```

## 💬 Natural Language Examples

### Infrastructure Management
- "Restart Galileo Notifications in staging"
- "Scale payment processor to 5 instances in prod"
- "Show status of all services in prod"
- "Deploy version 2.4.1 to staging"

### Security Operations
- "Show critical alerts from last hour"
- "Isolate CORPEFT-SQL01 immediately"
- "Enable DDoS protection on main site"
- "Check compliance status for PCI scope"

### Networking
- "Show VPN tunnel status"
- "Test connectivity from Azure to on-prem"
- "Update firewall to allow Jenkins CI"
- "Show bandwidth usage for main interconnect"

### Observability
- "Show errors for payment service in last 30 minutes"
- "Get CPU metrics for Galileo in prod"
- "Trace slow requests in the API gateway"

## 🛡️ Safety Features

### Environment Guardrails
- **Dev**: Unrestricted operations
- **Staging**: Confirmation for destructive actions
- **Prod**: Strict confirmations + audit trail

### Operation Classes
- **Read-only**: Status, logs, metrics
- **Operator**: Restart, scale, isolate
- **Admin**: Deploy, delete, modify infrastructure

### Audit Trail
Every operation logged with:
- Who (user/session)
- What (operation + parameters)
- When (timestamp)
- Where (environment/provider)
- Result (success/failure + details)

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   cd platform-control-plane
   pip install -r requirements.txt
   ```

2. **Configure domains and providers**:
   ```bash
   cp config/domains.example.yml config/domains.yml
   cp config/providers.example.yml config/providers.yml
   # Edit with your actual resource mappings
   ```

3. **Set up credentials**:
   ```bash
   # AWS
   export PLATFORM_AWS_PROD_ROLE="arn:aws:iam::654654560452:role/platform-control"
   export PLATFORM_AWS_STAGING_ROLE="arn:aws:iam::381492229443:role/platform-control"
   
   # Azure
   export PLATFORM_AZURE_CLIENT_ID="..."
   export PLATFORM_AZURE_CLIENT_SECRET="..."
   
   # SentinelOne
   export SENTINELONE_API_TOKEN="..."
   ```

4. **Run the MCP server**:
   ```bash
   python -m mcp_server.main
   ```

5. **Add to Cursor MCP config**:
   ```json
   {
     "platform-hub": {
       "command": "python",
       "args": ["-m", "mcp_server.main"],
       "cwd": "C:/path/to/platform-control-plane"
     }
   }
   ```

## 📊 Supported Operations

| Category | Operations | Providers |
|----------|------------|-----------|
| **Compute** | scale, restart, deploy, terminate | AWS, Azure, GCP |
| **Database** | backup, restore, failover, resize | AWS RDS, Azure SQL, Cloud SQL |
| **Security** | isolate, scan, patch, audit | SentinelOne, Defender, GuardDuty |
| **Network** | vpn_status, firewall_update, dns_update | Cisco, Azure, AWS |
| **Storage** | resize, backup, replicate | S3, Blob, GCS |
| **Monitoring** | get_alerts, ack_alert, create_dashboard | CloudWatch, Azure Monitor, Stackdriver |

## 🔌 Extending the Platform

### Adding a New Provider

1. Create `providers/newvendor_provider.py`
2. Implement required interfaces from `providers/base.py`
3. Update `config/providers.yml`
4. Map resources in `config/domains.yml`

### Adding New Tools

1. Create tool function in appropriate `tools/*.py`
2. Register with MCP in `main.py`
3. Update documentation

## 📈 Roadmap

- [ ] Phase 1: Core infrastructure operations (AWS, Azure)
- [ ] Phase 2: Security integration (SentinelOne, Cisco)
- [ ] Phase 3: Observability (metrics, logs, traces)
- [ ] Phase 4: Cost management
- [ ] Phase 5: Compliance automation
- [ ] Phase 6: GitOps integration

## 🤝 Contributing

This platform follows a provider-agnostic architecture. When contributing:
1. Keep provider-specific logic in provider modules
2. Use canonical references in tools
3. Add comprehensive error handling
4. Update tests and documentation

## 📝 License

MIT
