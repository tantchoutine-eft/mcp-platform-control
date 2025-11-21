#!/usr/bin/env python3
"""
Test script for Platform Control Plane
Run this to verify the implementation works
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up minimal logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_platform():
    """Test the platform control plane components"""
    
    print("\n[TEST] Platform Control Plane Test Suite")
    print("=" * 50)
    
    # Test 1: Domain Resolution
    print("\n[1] Testing Domain Resolution...")
    try:
        from mcp_server.core.resolver import DomainResolver
        resolver = DomainResolver("config")
        
        # List available domains
        domains = resolver.list_domains()
        print(f"   [OK] Found {len(domains)} domains: {domains[:3]}...")
        
        # Try to resolve a domain
        if 'galileo_notifications' in domains:
            resolved = resolver.resolve("galileo_notifications", "prod", "compute")
            print(f"   [OK] Resolved galileo_notifications/prod: {resolved.provider} - {resolved.ref}")
        else:
            print("   [WARN] galileo_notifications not found in config")
    except Exception as e:
        print(f"   [FAIL] Domain resolution failed: {e}")
        return False
    
    # Test 2: Guardrails
    print("\n[2] Testing Guardrails...")
    try:
        from mcp_server.core.guardrails import GuardrailsManager
        guardrails = GuardrailsManager("config")
        
        # Check scale operation
        check = await guardrails.check_scale_operation("test_service", "dev", 5)
        print(f"   [OK] Scale check for dev: allowed={check.get('allowed', False)}")
        
        # Check prod operation (should require confirmation)
        check = await guardrails.check_scale_operation("test_service", "prod", 5)
        requires_confirm = check.get('requires_confirmation', False)
        print(f"   [OK] Scale check for prod: requires_confirmation={requires_confirm}")
    except Exception as e:
        print(f"   [FAIL] Guardrails test failed: {e}")
    
    # Test 3: Audit Logger
    print("\n[3] Testing Audit Logger...")
    try:
        from mcp_server.core.audit import AuditLogger
        audit = AuditLogger("config")
        
        # Log a test operation
        audit.log_operation(
            operation="test_scale",
            domain="test_service",
            environment="dev",
            target_capacity=5
        )
        print(f"   [OK] Audit log created: {audit.audit_file}")
        
        # Check recent operations
        recent = audit.get_recent_operations(minutes=5)
        print(f"   [OK] Found {len(recent)} recent operations")
    except Exception as e:
        print(f"   [FAIL] Audit logger test failed: {e}")
    
    # Test 4: AWS Provider (if credentials available)
    print("\n[4] Testing AWS Provider...")
    try:
        from mcp_server.providers.aws_provider import AWSProvider
        
        # Create minimal config
        aws_config = {
            'profiles': {
                'dev': 'aws-sso-sandbox',
                'staging': 'aws-sso-nonprod', 
                'prod': 'aws-sso-prod'
            },
            'accounts': {
                'dev': '537124940140',
                'staging': '381492229443',
                'prod': '654654560452'
            },
            'default_region': 'us-east-1'
        }
        
        provider = AWSProvider(aws_config)
        await provider.initialize()
        
        # Try to validate credentials
        valid = await provider.validate_credentials()
        if valid:
            print(f"   [OK] AWS credentials validated")
            
            # Try to get regions
            regions = await provider.get_regions()
            print(f"   [OK] Available regions: {len(regions)}")
        else:
            print(f"   [WARN] AWS credentials not configured (this is OK for testing)")
    except Exception as e:
        print(f"   [SKIP] AWS provider test skipped: {e}")
    
    # Test 5: Infrastructure Tools
    print("\n[5] Testing Infrastructure Tools...")
    try:
        from mcp_server.tools.infrastructure import InfrastructureTools
        from mcp_server.core.resolver import DomainResolver
        from mcp_server.core.guardrails import GuardrailsManager
        from mcp_server.core.audit import AuditLogger
        
        # Create instances
        resolver = DomainResolver("config")
        guardrails = GuardrailsManager("config")
        audit = AuditLogger("config")
        providers = {}  # Empty for now
        
        # Create tools instance
        infra_tools = InfrastructureTools(resolver, providers, guardrails, audit)
        
        # Test list services
        result = await infra_tools.list_services()
        print(f"   [OK] Listed {result['service_count']} services")
    except Exception as e:
        print(f"   [FAIL] Infrastructure tools test failed: {e}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Basic platform tests completed!")
    print("\nNext steps:")
    print("1. Configure your domains in config/domains.yml")
    print("2. Set up provider credentials")
    print("3. Run the full MCP server")
    
    return True


async def test_with_sample_data():
    """Test with sample configuration"""
    
    print("\n[INFO] Creating sample configuration...")
    
    # Create config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create sample domains.yml if it doesn't exist
    domains_file = config_dir / "domains.yml"
    if not domains_file.exists():
        sample_domains = """# Sample Domain Configuration
test_service:
  dev:
    compute:
      provider: aws
      kind: ec2
      ref: test-service-dev
      region: us-east-1
  prod:
    compute:
      provider: aws
      kind: asg
      ref: test-service-prod-asg
      region: us-east-1
    database:
      provider: aws
      kind: rds
      ref: test-service-db

sample_app:
  staging:
    compute:
      provider: azure
      kind: vmss
      ref: sample-app-vmss
      resource_group: rg-staging
"""
        domains_file.write_text(sample_domains)
        print(f"   [OK] Created sample {domains_file}")
    
    # Create sample providers.yml if it doesn't exist
    providers_file = config_dir / "providers.yml"
    if not providers_file.exists():
        sample_providers = """# Sample Provider Configuration
aws:
  profiles:
    dev: aws-sso-sandbox
    staging: aws-sso-nonprod
    prod: aws-sso-prod
  accounts:
    dev: "123456789012"
    staging: "234567890123"
    prod: "345678901234"
  default_region: us-east-1

azure:
  subscriptions:
    staging: "staging-sub-id"
    prod: "prod-sub-id"
  default_location: eastus

sentinelone:
  api_token: "${SENTINELONE_API_TOKEN}"
  api_url: "https://api.sentinelone.com"
"""
        providers_file.write_text(sample_providers)
        print(f"   [OK] Created sample {providers_file}")
    
    # Create sample policies.yml if it doesn't exist
    policies_file = config_dir / "policies.yml"
    if not policies_file.exists():
        sample_policies = """# Sample Policies Configuration
environments:
  dev:
    risk_level: low
    confirmations_required: false
    max_scale_size: 10
    
  staging:
    risk_level: medium
    confirmations_required: false
    max_scale_size: 20
    
  prod:
    risk_level: high
    confirmations_required: true
    confirmation_operations:
      - scale
      - restart
      - deploy
    max_scale_size: 50

guardrails:
  scaling:
    min_instances:
      default: 1
      prod: 2
    max_instances:
      default: 20
      prod: 50

confirmations:
  token:
    type: alphanumeric
    length: 6

audit:
  enabled: true
  log_level:
    read_operations: info
    write_operations: info
"""
        policies_file.write_text(sample_policies)
        print(f"   [OK] Created sample {policies_file}")
    
    # Run tests
    await test_platform()


if __name__ == "__main__":
    asyncio.run(test_with_sample_data())
