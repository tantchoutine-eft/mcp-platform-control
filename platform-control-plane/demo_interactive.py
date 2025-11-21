#!/usr/bin/env python3
"""
Interactive demo of the Platform Control Plane
Shows how natural language commands map to infrastructure operations
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server_simple import SimplePlatformHub


async def demo():
    """Run an interactive demo"""
    
    print("\n" + "=" * 60)
    print("     PLATFORM CONTROL PLANE - Live Demo")
    print("=" * 60)
    print("\nThis demo shows how natural language maps to operations.")
    print("Instead of vendor-specific commands, you use simple verbs.\n")
    
    # Initialize hub
    hub = SimplePlatformHub("config")
    
    # Validate AWS
    if 'aws' in hub.providers:
        valid = await hub.providers['aws'].validate_credentials()
        if valid:
            print("[OK] AWS credentials active\n")
        else:
            print("[WARN] AWS credentials not configured\n")
    
    demos = [
        {
            'title': 'List All Services',
            'natural': '"Show me all services in production"',
            'traditional': 'aws autoscaling describe-auto-scaling-groups --profile aws-sso-prod',
            'command': 'list_services',
            'args': {'environment': 'prod'}
        },
        {
            'title': 'Check Service Status',
            'natural': '"What\'s the status of Galileo Notifications in production?"',
            'traditional': 'aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name galileo-notify-asg-prod --profile aws-sso-prod',
            'command': 'get_status',
            'args': {'domain': 'galileo_notifications', 'environment': 'prod'}
        },
        {
            'title': 'Scale Service (with Confirmation)',
            'natural': '"Scale Galileo Notifications to 5 instances in production"',
            'traditional': 'aws autoscaling set-desired-capacity --auto-scaling-group-name galileo-notify-asg-prod --desired-capacity 5 --profile aws-sso-prod',
            'command': 'scale_service',
            'args': {'domain': 'galileo_notifications', 'environment': 'prod', 'capacity': 5}
        }
    ]
    
    for demo_item in demos:
        print(f"\n{'=' * 60}")
        print(f"Demo: {demo_item['title']}")
        print(f"{'=' * 60}")
        
        print(f"\nNatural Language:")
        print(f"  {demo_item['natural']}")
        
        print(f"\nTraditional Approach:")
        print(f"  {demo_item['traditional']}")
        
        print(f"\nPlatform Hub Command:")
        print(f"  {demo_item['command']}({demo_item['args']})")
        
        print(f"\nExecuting...")
        result = await hub.handle_command(demo_item['command'], demo_item['args'])
        
        if result.get('success'):
            print(f"[SUCCESS]")
            # Show key results
            if 'service_count' in result:
                print(f"  Found {result['service_count']} services")
                if result.get('services'):
                    for svc in result['services'][:3]:
                        print(f"    - {svc['domain']}/{svc['environment']}")
            elif 'status' in result:
                print(f"  Status: {result['status']}")
            elif 'message' in result:
                print(f"  {result['message']}")
        elif result.get('requires_confirmation'):
            print(f"[CONFIRMATION REQUIRED]")
            print(f"  Token: {result['confirmation_token']}")
            print(f"  Reason: {result.get('reason', 'Safety check')}")
        else:
            print(f"[ERROR] {result.get('error', 'Unknown error')}")
        
        # Small delay between demos
        if demo_item != demos[-1]:
            await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. One interface for ALL providers (AWS, Azure, GCP, etc.)")
    print("2. Natural language commands, not vendor-specific syntax")
    print("3. Built-in safety with confirmations for production")
    print("4. Automatic audit trail for compliance")
    print("\nTo run interactive mode: python mcp_server_simple.py")


if __name__ == "__main__":
    asyncio.run(demo())
