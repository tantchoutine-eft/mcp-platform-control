#!/usr/bin/env python3
"""
Test the interactive platform hub with automated commands
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server_simple import SimplePlatformHub


async def test_commands():
    """Test various platform commands"""
    
    print("\n[TEST] Platform Hub Command Testing")
    print("=" * 50)
    
    # Initialize hub
    hub = SimplePlatformHub("config")
    
    # Test 1: List services
    print("\n[1] Testing list services...")
    result = await hub.handle_command('list_services', {})
    print(f"   Found {result.get('service_count', 0)} services")
    if result.get('services'):
        for svc in result['services'][:3]:
            print(f"   - {svc['domain']}/{svc['environment']}")
    
    # Test 2: Get status
    print("\n[2] Testing get status...")
    result = await hub.handle_command('get_status', {
        'domain': 'galileo_notifications',
        'environment': 'prod'
    })
    if result.get('success'):
        print(f"   Status: {result.get('status')}")
        instances = result.get('instances', {})
        print(f"   Instances: {instances.get('total', 0)} total, {instances.get('healthy', 0)} healthy")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 3: Scale service (should require confirmation in prod)
    print("\n[3] Testing scale service...")
    result = await hub.handle_command('scale_service', {
        'domain': 'galileo_notifications',
        'environment': 'prod',
        'capacity': 5
    })
    if result.get('requires_confirmation'):
        print(f"   Confirmation required: {result.get('confirmation_token')}")
    elif result.get('success'):
        print(f"   Scaling initiated")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 4: Get logs
    print("\n[4] Testing get logs...")
    result = await hub.handle_command('get_logs', {
        'domain': 'galileo_notifications',
        'environment': 'prod',
        'last_minutes': 5
    })
    if result.get('success'):
        print(f"   Retrieved {result.get('log_count', 0)} log entries")
    else:
        print(f"   Error: {result.get('error')}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Command tests completed")


if __name__ == "__main__":
    asyncio.run(test_commands())



