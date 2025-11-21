#!/usr/bin/env python3
"""
Simplified Platform Control Plane MCP Server
Can be run standalone or with MCP protocol
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from mcp_server.core.resolver import DomainResolver
from mcp_server.core.guardrails import GuardrailsManager
from mcp_server.core.audit import AuditLogger
from mcp_server.providers.aws_provider import AWSProvider
from mcp_server.tools.infrastructure import InfrastructureTools


class SimplePlatformHub:
    """Simplified Platform Control Plane"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        
        logger.info(f"Initializing Platform Hub with config from {config_path}")
        
        # Initialize core components
        self.resolver = DomainResolver(config_path)
        self.guardrails = GuardrailsManager(config_path)
        self.audit = AuditLogger(config_path)
        
        # Initialize providers
        self.providers = {}
        self._init_providers()
        
        # Initialize tools
        self.infra_tools = InfrastructureTools(
            self.resolver, self.providers, self.guardrails, self.audit
        )
        
        logger.info("Platform Hub initialized successfully")
    
    def _init_providers(self):
        """Initialize configured providers"""
        provider_config = self.resolver.providers
        
        # AWS Provider
        if 'aws' in provider_config:
            try:
                aws = AWSProvider(provider_config['aws'])
                asyncio.create_task(aws.initialize())
                self.providers['aws'] = aws
                logger.info("AWS provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AWS provider: {e}")
    
    async def handle_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a platform command"""
        
        logger.info(f"Handling command: {command} with args: {args}")
        
        try:
            if command == "get_status":
                result = await self.infra_tools.get_status(
                    args.get('domain'),
                    args.get('environment'),
                    args.get('resource_type', 'compute')
                )
            
            elif command == "scale_service":
                result = await self.infra_tools.scale_service(
                    args.get('domain'),
                    args.get('environment'),
                    args.get('capacity')
                )
            
            elif command == "restart_service":
                result = await self.infra_tools.restart_service(
                    args.get('domain'),
                    args.get('environment')
                )
            
            elif command == "list_services":
                result = await self.infra_tools.list_services(
                    args.get('environment')
                )
            
            elif command == "get_logs":
                result = await self.infra_tools.get_logs(
                    args.get('domain'),
                    args.get('environment'),
                    args.get('last_minutes', 30),
                    args.get('severity'),
                    args.get('search')
                )
            
            else:
                result = {
                    'success': False,
                    'error': f'Unknown command: {command}'
                }
            
            logger.info(f"Command completed: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'args': args
            }
    
    async def interactive_mode(self):
        """Run in interactive mode for testing"""
        
        print("\n===============================================")
        print("    Platform Control Plane - Interactive Mode")
        print("===============================================")
        print("\nAvailable commands:")
        print("  status <domain> <env>    - Get service status")
        print("  scale <domain> <env> <n> - Scale service")
        print("  restart <domain> <env>   - Restart service")
        print("  list [env]               - List services")
        print("  logs <domain> <env>      - Get service logs")
        print("  help                     - Show this help")
        print("  exit                     - Exit")
        print("\nExample: status galileo_notifications prod")
        print("         scale galileo_notifications staging 3")
        print("===============================================\n")
        
        while True:
            try:
                # Get input
                user_input = input("platform> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split()
                cmd = parts[0].lower()
                
                if cmd == 'exit':
                    print("Goodbye!")
                    break
                
                elif cmd == 'help':
                    print("\nCommands:")
                    print("  status <domain> <env>    - Get service status")
                    print("  scale <domain> <env> <n> - Scale service")
                    print("  restart <domain> <env>   - Restart service")
                    print("  list [env]               - List services")
                    print("  logs <domain> <env>      - Get service logs")
                    continue
                
                elif cmd == 'status' and len(parts) >= 3:
                    result = await self.handle_command('get_status', {
                        'domain': parts[1],
                        'environment': parts[2]
                    })
                
                elif cmd == 'scale' and len(parts) >= 4:
                    result = await self.handle_command('scale_service', {
                        'domain': parts[1],
                        'environment': parts[2],
                        'capacity': int(parts[3])
                    })
                
                elif cmd == 'restart' and len(parts) >= 3:
                    result = await self.handle_command('restart_service', {
                        'domain': parts[1],
                        'environment': parts[2]
                    })
                
                elif cmd == 'list':
                    env = parts[1] if len(parts) > 1 else None
                    result = await self.handle_command('list_services', {
                        'environment': env
                    })
                
                elif cmd == 'logs' and len(parts) >= 3:
                    result = await self.handle_command('get_logs', {
                        'domain': parts[1],
                        'environment': parts[2],
                        'last_minutes': 30
                    })
                
                else:
                    print(f"Invalid command. Type 'help' for available commands.")
                    continue
                
                # Display result
                if result.get('success'):
                    print("\n[SUCCESS]")
                    # Pretty print the result
                    for key, value in result.items():
                        if key == 'success':
                            continue
                        if isinstance(value, (dict, list)):
                            print(f"{key}:")
                            print(json.dumps(value, indent=2))
                        else:
                            print(f"{key}: {value}")
                else:
                    print(f"\n[ERROR] {result.get('error', 'Unknown error')}")
                    if 'requires_confirmation' in result:
                        print(f"Confirmation required. Token: {result.get('confirmation_token')}")
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' to quit")
            except Exception as e:
                print(f"[ERROR] {e}")


async def main():
    """Main entry point"""
    
    # Check if MCP mode or interactive
    if len(sys.argv) > 1 and sys.argv[1] == '--mcp':
        print("MCP mode not yet implemented. Use interactive mode.")
        return
    
    # Run in interactive mode
    hub = SimplePlatformHub("config")
    
    # Validate AWS credentials
    if 'aws' in hub.providers:
        if await hub.providers['aws'].validate_credentials():
            print("[OK] AWS credentials validated")
        else:
            print("[WARN] AWS credentials not configured")
    
    await hub.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())



