#!/usr/bin/env python3
"""
Platform Control Plane MCP Server
Single natural language interface for multi-cloud and multi-vendor infrastructure
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import Server
from mcp.server import Request, Response
from mcp.types import Tool, ToolCall, TextContent

# Import core components
from mcp_server.core.resolver import DomainResolver
from mcp_server.core.guardrails import GuardrailsManager
from mcp_server.core.audit import AuditLogger

# Import providers
from mcp_server.providers.aws_provider import AWSProvider
from mcp_server.providers.azure_provider import AzureProvider
from mcp_server.providers.sentinelone_provider import SentinelOneProvider
from mcp_server.providers.cisco_provider import CiscoProvider

# Import tools
from mcp_server.tools.infrastructure import InfrastructureTools
from mcp_server.tools.security import SecurityTools
from mcp_server.tools.networking import NetworkingTools
from mcp_server.tools.observability import ObservabilityTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlatformControlPlane:
    """Main Platform Control Plane MCP Server"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.server = Server("platform-control-plane")
        
        # Initialize components
        self.resolver = DomainResolver(config_path)
        self.guardrails = GuardrailsManager(config_path)
        self.audit = AuditLogger(config_path)
        
        # Initialize providers
        self.providers = {}
        self._init_providers()
        
        # Initialize tool modules
        self.infra_tools = InfrastructureTools(
            self.resolver, self.providers, self.guardrails, self.audit
        )
        self.security_tools = SecurityTools(
            self.resolver, self.providers, self.guardrails, self.audit
        )
        self.network_tools = NetworkingTools(
            self.resolver, self.providers, self.guardrails, self.audit
        )
        self.observability_tools = ObservabilityTools(
            self.resolver, self.providers, self.guardrails, self.audit
        )
        
        # Register tools with MCP
        self._register_tools()
    
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
        
        # Azure Provider
        if 'azure' in provider_config:
            try:
                azure = AzureProvider(provider_config['azure'])
                asyncio.create_task(azure.initialize())
                self.providers['azure'] = azure
                logger.info("Azure provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure provider: {e}")
        
        # SentinelOne Provider
        if 'sentinelone' in provider_config:
            try:
                s1 = SentinelOneProvider(provider_config['sentinelone'])
                asyncio.create_task(s1.initialize())
                self.providers['sentinelone'] = s1
                logger.info("SentinelOne provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SentinelOne provider: {e}")
        
        # Cisco Provider
        if 'cisco' in provider_config:
            try:
                cisco = CiscoProvider(provider_config['cisco'])
                asyncio.create_task(cisco.initialize())
                self.providers['cisco'] = cisco
                logger.info("Cisco provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Cisco provider: {e}")
    
    def _register_tools(self):
        """Register all tools with MCP server"""
        
        # Infrastructure Tools
        self.server.add_tool(Tool(
            name="get_infrastructure_status",
            description="Get status of any infrastructure service. Example: 'Show status of Galileo Notifications in prod'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name (e.g., 'galileo_notifications')"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment (prod, staging, dev)"
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Resource type (compute, database, cache)",
                        "default": "compute"
                    }
                },
                "required": ["domain", "environment"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="scale_service",
            description="Scale infrastructure service to specified capacity. Example: 'Scale payment processor to 5 instances in prod'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    },
                    "capacity": {
                        "type": "integer",
                        "description": "Target number of instances"
                    }
                },
                "required": ["domain", "environment", "capacity"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="restart_service",
            description="Restart/reboot infrastructure service. Example: 'Restart API gateway in staging'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    }
                },
                "required": ["domain", "environment"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="deploy_service",
            description="Deploy new version to service. Example: 'Deploy version 2.4.1 to Galileo in staging'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version to deploy"
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Deployment strategy (rolling, canary, blue-green)",
                        "default": "rolling"
                    }
                },
                "required": ["domain", "environment", "version"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="get_service_logs",
            description="Get logs for a service. Example: 'Show errors from payment service in last 30 minutes'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    },
                    "last_minutes": {
                        "type": "integer",
                        "description": "How many minutes of logs to retrieve",
                        "default": 30
                    },
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity (ERROR, WARNING, INFO)"
                    },
                    "search": {
                        "type": "string",
                        "description": "Search pattern in logs"
                    }
                },
                "required": ["domain", "environment"]
            }
        ))
        
        # Security Tools
        self.server.add_tool(Tool(
            name="get_security_alerts",
            description="Get security alerts from any source. Example: 'Show critical SentinelOne alerts from last hour'",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Alert source (sentinelone, guardduty, azure_sentinel)"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Minimum severity (critical, high, medium, low)"
                    },
                    "last_minutes": {
                        "type": "integer",
                        "description": "Time window in minutes",
                        "default": 60
                    }
                },
                "required": ["source"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="isolate_endpoint",
            description="Isolate an endpoint from network. Example: 'Isolate CORPEFT-SQL01 immediately'",
            parameters={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to isolate"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for isolation"
                    }
                },
                "required": ["hostname"]
            }
        ))
        
        # Network Tools
        self.server.add_tool(Tool(
            name="get_vpn_status",
            description="Get VPN tunnel status. Example: 'Show VPN status for Azure to datacenter link'",
            parameters={
                "type": "object",
                "properties": {
                    "link_name": {
                        "type": "string",
                        "description": "VPN link name from config"
                    }
                },
                "required": ["link_name"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="test_connectivity",
            description="Test network connectivity. Example: 'Test connection from Azure hub to on-prem firewall'",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source location"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination location"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port to test"
                    }
                },
                "required": ["source", "destination"]
            }
        ))
        
        # Observability Tools
        self.server.add_tool(Tool(
            name="get_metrics",
            description="Get metrics for a service. Example: 'Show CPU usage for Galileo in prod'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    },
                    "metric_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to retrieve (CPU, Memory, NetworkIn, etc.)"
                    },
                    "last_minutes": {
                        "type": "integer",
                        "description": "Time window in minutes",
                        "default": 60
                    }
                },
                "required": ["domain", "environment", "metric_names"]
            }
        ))
        
        # Management Tools
        self.server.add_tool(Tool(
            name="list_services",
            description="List all managed services. Example: 'Show all services in prod'",
            parameters={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Filter by environment"
                    }
                }
            }
        ))
        
        self.server.add_tool(Tool(
            name="health_check",
            description="Perform comprehensive health check. Example: 'Health check for payment system in prod'",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain name"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment"
                    }
                },
                "required": ["domain", "environment"]
            }
        ))
        
        # Set up tool handlers
        @self.server.call_tool
        async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> TextContent:
            """Route tool calls to appropriate handlers"""
            
            try:
                # Infrastructure tools
                if name == "get_infrastructure_status":
                    result = await self.infra_tools.get_status(**arguments)
                elif name == "scale_service":
                    result = await self.infra_tools.scale_service(**arguments)
                elif name == "restart_service":
                    result = await self.infra_tools.restart_service(**arguments)
                elif name == "deploy_service":
                    result = await self.infra_tools.deploy_service(**arguments)
                elif name == "get_service_logs":
                    result = await self.infra_tools.get_logs(**arguments)
                
                # Security tools
                elif name == "get_security_alerts":
                    result = await self.security_tools.get_alerts(**arguments)
                elif name == "isolate_endpoint":
                    result = await self.security_tools.isolate_endpoint(**arguments)
                
                # Network tools
                elif name == "get_vpn_status":
                    result = await self.network_tools.get_vpn_status(**arguments)
                elif name == "test_connectivity":
                    result = await self.network_tools.test_connectivity(**arguments)
                
                # Observability tools
                elif name == "get_metrics":
                    result = await self.observability_tools.get_metrics(**arguments)
                
                # Management tools
                elif name == "list_services":
                    result = await self.infra_tools.list_services(**arguments)
                elif name == "health_check":
                    result = await self.infra_tools.health_check(**arguments)
                
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return TextContent(text=json.dumps(result, indent=2))
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return TextContent(text=json.dumps({
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }, indent=2))
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Platform Control Plane MCP Server")
        logger.info(f"Config path: {self.config_path}")
        logger.info(f"Available providers: {list(self.providers.keys())}")
        
        # Validate provider credentials
        for name, provider in self.providers.items():
            if await provider.validate_credentials():
                logger.info(f"✓ {name} credentials validated")
            else:
                logger.error(f"✗ {name} credentials invalid")
        
        # Start server
        await self.server.run()


if __name__ == "__main__":
    # Get config path from environment or use default
    config_path = os.environ.get("PLATFORM_CONFIG_PATH", "config")
    
    # Create and run server
    platform = PlatformControlPlane(config_path)
    asyncio.run(platform.run())
