"""
Infrastructure management tools for Platform Control Plane
Provides verb-based, provider-agnostic operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..core.resolver import DomainResolver, ResolvedResource
from ..core.guardrails import GuardrailsManager
from ..core.audit import AuditLogger
from ..providers.base import OperationResult, ServiceStatus


class InfrastructureTools:
    """Verb-based infrastructure operations"""
    
    def __init__(self, resolver: DomainResolver, providers: Dict[str, Any],
                 guardrails: GuardrailsManager, audit: AuditLogger):
        self.resolver = resolver
        self.providers = providers
        self.guardrails = guardrails
        self.audit = audit
    
    async def get_status(self, domain: str, environment: str, 
                        resource_type: str = 'compute') -> Dict[str, Any]:
        """
        Get status of infrastructure resource
        
        Examples:
            get_status("galileo_notifications", "prod")
            get_status("corp_infrastructure", "prod", "domain_controllers")
        """
        
        # Resolve domain to physical resource
        resolved = self.resolver.resolve(domain, environment, resource_type)
        
        # Get appropriate provider
        provider = self.providers.get(resolved.provider)
        if not provider:
            return {
                'error': f"Provider '{resolved.provider}' not available",
                'success': False
            }
        
        # Log operation
        self.audit.log_operation(
            operation="get_status",
            domain=domain,
            environment=environment,
            resource_type=resource_type,
            provider=resolved.provider,
            user=self.audit.current_user
        )
        
        try:
            # Get status from provider
            compute_ref = self.resolver.to_compute_ref(resolved)
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Getting status for {compute_ref.ref} in {compute_ref.provider}")
            
            status = await provider.get_status(compute_ref)
            
            return {
                'success': True,
                'domain': domain,
                'environment': environment,
                'status': status.status.value,
                'instances': {
                    'total': status.instance_count,
                    'healthy': status.healthy_count,
                    'unhealthy': status.unhealthy_count
                },
                'provider': resolved.provider,
                'region': resolved.region,
                'last_updated': status.last_updated.isoformat(),
                'metadata': status.metadata
            }
        except Exception as e:
            self.audit.log_error(
                operation="get_status",
                error=str(e),
                domain=domain,
                environment=environment
            )
            return {
                'success': False,
                'error': str(e),
                'domain': domain,
                'environment': environment
            }
    
    async def scale_service(self, domain: str, environment: str, capacity: int,
                          resource_type: str = 'compute') -> Dict[str, Any]:
        """
        Scale infrastructure resource to specified capacity
        
        Examples:
            scale_service("galileo_notifications", "prod", 5)
            scale_service("api_gateway", "staging", 2)
        """
        
        # Check guardrails
        check = await self.guardrails.check_scale_operation(
            domain=domain,
            environment=environment,
            target_capacity=capacity
        )
        
        if not check['allowed']:
            return {
                'success': False,
                'error': check['reason'],
                'requires_confirmation': check.get('requires_confirmation', False),
                'confirmation_token': check.get('token')
            }
        
        # Resolve domain
        resolved = self.resolver.resolve(domain, environment, resource_type)
        
        # Get provider
        provider = self.providers.get(resolved.provider)
        if not provider:
            return {
                'error': f"Provider '{resolved.provider}' not available",
                'success': False
            }
        
        # Get current status first
        compute_ref = self.resolver.to_compute_ref(resolved)
        current_status = await provider.get_status(compute_ref)
        current_capacity = current_status.instance_count
        
        # Log operation
        self.audit.log_operation(
            operation="scale_service",
            domain=domain,
            environment=environment,
            resource_type=resource_type,
            provider=resolved.provider,
            current_capacity=current_capacity,
            target_capacity=capacity,
            user=self.audit.current_user
        )
        
        try:
            # Perform scaling
            result = await provider.scale(compute_ref, capacity)
            
            if result.success:
                return {
                    'success': True,
                    'domain': domain,
                    'environment': environment,
                    'message': f"Scaling {domain} in {environment} from {current_capacity} to {capacity} instances",
                    'previous_capacity': current_capacity,
                    'new_capacity': capacity,
                    'provider': resolved.provider,
                    'details': result.details
                }
            else:
                return {
                    'success': False,
                    'error': result.error,
                    'message': result.message,
                    'domain': domain,
                    'environment': environment
                }
        except Exception as e:
            self.audit.log_error(
                operation="scale_service",
                error=str(e),
                domain=domain,
                environment=environment
            )
            return {
                'success': False,
                'error': str(e),
                'domain': domain,
                'environment': environment
            }
    
    async def restart_service(self, domain: str, environment: str,
                            resource_type: str = 'compute') -> Dict[str, Any]:
        """
        Restart infrastructure resource
        
        Examples:
            restart_service("galileo_notifications", "staging")
            restart_service("corp_infrastructure", "prod", "domain_controllers")
        """
        
        # Check guardrails
        check = await self.guardrails.check_restart_operation(
            domain=domain,
            environment=environment
        )
        
        if not check['allowed']:
            return {
                'success': False,
                'error': check['reason'],
                'requires_confirmation': check.get('requires_confirmation', False),
                'confirmation_token': check.get('token')
            }
        
        # Resolve domain
        resolved = self.resolver.resolve(domain, environment, resource_type)
        
        # Get provider
        provider = self.providers.get(resolved.provider)
        if not provider:
            return {
                'error': f"Provider '{resolved.provider}' not available",
                'success': False
            }
        
        # Log operation
        self.audit.log_operation(
            operation="restart_service",
            domain=domain,
            environment=environment,
            resource_type=resource_type,
            provider=resolved.provider,
            user=self.audit.current_user
        )
        
        try:
            # Perform restart
            compute_ref = self.resolver.to_compute_ref(resolved)
            result = await provider.restart(compute_ref)
            
            if result.success:
                return {
                    'success': True,
                    'domain': domain,
                    'environment': environment,
                    'message': f"Restarting {domain} in {environment}",
                    'provider': resolved.provider,
                    'details': result.details
                }
            else:
                return {
                    'success': False,
                    'error': result.error,
                    'message': result.message,
                    'domain': domain,
                    'environment': environment
                }
        except Exception as e:
            self.audit.log_error(
                operation="restart_service",
                error=str(e),
                domain=domain,
                environment=environment
            )
            return {
                'success': False,
                'error': str(e),
                'domain': domain,
                'environment': environment
            }
    
    async def deploy_service(self, domain: str, environment: str, version: str,
                           strategy: str = 'rolling', **kwargs) -> Dict[str, Any]:
        """
        Deploy new version to service
        
        Examples:
            deploy_service("galileo_notifications", "staging", "v2.4.1")
            deploy_service("api_gateway", "prod", "v1.2.3", strategy="canary")
        """
        
        # Check guardrails
        check = await self.guardrails.check_deploy_operation(
            domain=domain,
            environment=environment,
            version=version
        )
        
        if not check['allowed']:
            return {
                'success': False,
                'error': check['reason'],
                'requires_confirmation': check.get('requires_confirmation', False),
                'confirmation_token': check.get('token')
            }
        
        # Resolve domain
        resolved = self.resolver.resolve(domain, environment, 'compute')
        
        # Get provider
        provider = self.providers.get(resolved.provider)
        if not provider:
            return {
                'error': f"Provider '{resolved.provider}' not available",
                'success': False
            }
        
        # Log operation
        self.audit.log_operation(
            operation="deploy_service",
            domain=domain,
            environment=environment,
            version=version,
            strategy=strategy,
            provider=resolved.provider,
            user=self.audit.current_user
        )
        
        try:
            # Perform deployment
            compute_ref = self.resolver.to_compute_ref(resolved)
            result = await provider.deploy(
                compute_ref, 
                version,
                strategy=strategy,
                **kwargs
            )
            
            if result.success:
                return {
                    'success': True,
                    'domain': domain,
                    'environment': environment,
                    'message': f"Deploying {version} to {domain} in {environment} using {strategy} strategy",
                    'version': version,
                    'strategy': strategy,
                    'provider': resolved.provider,
                    'details': result.details
                }
            else:
                return {
                    'success': False,
                    'error': result.error,
                    'message': result.message,
                    'domain': domain,
                    'environment': environment
                }
        except Exception as e:
            self.audit.log_error(
                operation="deploy_service",
                error=str(e),
                domain=domain,
                environment=environment,
                version=version
            )
            return {
                'success': False,
                'error': str(e),
                'domain': domain,
                'environment': environment
            }
    
    async def get_logs(self, domain: str, environment: str, 
                      last_minutes: int = 30,
                      severity: Optional[str] = None,
                      search: Optional[str] = None) -> Dict[str, Any]:
        """
        Get logs for a service
        
        Examples:
            get_logs("galileo_notifications", "prod", last_minutes=60)
            get_logs("api_gateway", "staging", severity="ERROR")
        """
        
        # Try to resolve monitoring config first, fall back to compute
        try:
            resolved = self.resolver.resolve(domain, environment, 'monitoring')
        except ValueError:
            try:
                resolved = self.resolver.resolve(domain, environment, 'compute')
            except ValueError as e:
                return {
                    'success': False,
                    'error': f"Could not resolve {domain}/{environment}",
                    'details': str(e)
                }
        
        # Get provider
        provider = self.providers.get(resolved.provider)
        
        if not provider:
            return {
                'error': f"No provider available for {domain}",
                'success': False
            }
        
        try:
            # Build log query
            log_config = self.resolver.domains[domain][environment].get('monitoring', {})
            log_group = log_config.get('log_group') or f"/aws/service/{domain}"
            
            # Get logs from provider
            if hasattr(provider, 'get_logs'):
                logs = await provider.get_logs(
                    log_group=log_group,
                    env=environment,
                    last_minutes=last_minutes,
                    filter_pattern=search
                )
                
                # Filter by severity if specified
                if severity and logs:
                    severity_upper = severity.upper()
                    logs = [
                        log for log in logs
                        if severity_upper in log.get('message', '').upper()
                    ]
                
                return {
                    'success': True,
                    'domain': domain,
                    'environment': environment,
                    'log_count': len(logs),
                    'time_range': f"Last {last_minutes} minutes",
                    'logs': logs[:1000]  # Limit response size
                }
            else:
                return {
                    'success': False,
                    'error': f"Provider {resolved.provider} doesn't support log retrieval"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'domain': domain,
                'environment': environment
            }
    
    async def list_services(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        List all services, optionally filtered by environment
        
        Examples:
            list_services()
            list_services("prod")
        """
        
        services = []
        
        for domain in self.resolver.list_domains():
            envs = self.resolver.list_environments(domain)
            
            if environment:
                if environment in envs:
                    envs = [environment]
                else:
                    continue
            
            for env in envs:
                try:
                    # Try to get basic info about the service
                    resources = self.resolver.list_resources(domain, env)
                    
                    service_info = {
                        'domain': domain,
                        'environment': env,
                        'resources': resources
                    }
                    
                    # Try to get compute status if available
                    if 'compute' in resources:
                        resolved = self.resolver.resolve(domain, env, 'compute')
                        service_info['provider'] = resolved.provider
                        service_info['region'] = resolved.region
                        service_info['kind'] = resolved.kind
                    
                    services.append(service_info)
                except Exception as e:
                    # Skip services that can't be resolved
                    continue
        
        return {
            'success': True,
            'service_count': len(services),
            'services': services
        }
    
    async def health_check(self, domain: str, environment: str) -> Dict[str, Any]:
        """
        Perform comprehensive health check on a service
        
        Examples:
            health_check("galileo_notifications", "prod")
        """
        
        health_status = {
            'domain': domain,
            'environment': environment,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Check compute health
        try:
            compute_status = await self.get_status(domain, environment, 'compute')
            health_status['checks']['compute'] = {
                'healthy': compute_status.get('instances', {}).get('unhealthy', 0) == 0,
                'details': compute_status
            }
        except:
            health_status['checks']['compute'] = {'healthy': False, 'error': 'Unable to check'}
        
        # Check database health if exists
        try:
            if 'database' in self.resolver.list_resources(domain, environment):
                resolved = self.resolver.resolve(domain, environment, 'database')
                provider = self.providers.get(resolved.provider)
                if provider and hasattr(provider, 'get_db_status'):
                    db_status = await provider.get_db_status(resolved.ref, environment)
                    health_status['checks']['database'] = {
                        'healthy': db_status.get('status') in ['available', 'running'],
                        'details': db_status
                    }
        except:
            pass
        
        # Overall health
        all_healthy = all(
            check.get('healthy', False) 
            for check in health_status['checks'].values()
        )
        
        health_status['overall_health'] = 'healthy' if all_healthy else 'unhealthy'
        health_status['success'] = True
        
        return health_status
