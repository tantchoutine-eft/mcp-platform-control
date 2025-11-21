"""
Domain-to-Provider Resolution Engine
Maps logical service names to physical resources across providers
"""

import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..providers.base import ComputeRef


@dataclass
class ResolvedResource:
    """Resolved resource with all necessary information"""
    domain: str
    environment: str
    resource_type: str  # compute, database, cache, etc.
    provider: str
    kind: str
    ref: str
    region: Optional[str] = None
    account: Optional[str] = None
    resource_group: Optional[str] = None
    subscription: Optional[str] = None
    project: Optional[str] = None
    metadata: Dict[str, Any] = None


class DomainResolver:
    """Resolves logical domains to physical resources"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.domains = self._load_domains()
        self.providers = self._load_providers()
        self.policies = self._load_policies()
        
        # Build reverse lookup index for faster resolution
        self._build_indices()
    
    def _load_domains(self) -> Dict[str, Any]:
        """Load domain configuration"""
        domains_file = self.config_path / "domains.yml"
        if not domains_file.exists():
            raise FileNotFoundError(f"Domains config not found: {domains_file}")
        
        with open(domains_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_providers(self) -> Dict[str, Any]:
        """Load provider configuration"""
        providers_file = self.config_path / "providers.yml"
        if not providers_file.exists():
            raise FileNotFoundError(f"Providers config not found: {providers_file}")
        
        with open(providers_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load policies configuration"""
        policies_file = self.config_path / "policies.yml"
        if policies_file.exists():
            with open(policies_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _build_indices(self):
        """Build lookup indices for faster resolution"""
        self.resource_index = {}  # ref -> (domain, env, type)
        self.provider_index = {}  # provider -> list of resources
        
        for domain, envs in self.domains.items():
            if isinstance(envs, dict):
                for env, resources in envs.items():
                    if isinstance(resources, dict):
                        for resource_type, config in resources.items():
                            if isinstance(config, dict) and 'ref' in config:
                                key = (config.get('provider'), config['ref'])
                                self.resource_index[key] = {
                                    'domain': domain,
                                    'environment': env,
                                    'resource_type': resource_type
                                }
                                
                                provider = config.get('provider')
                                if provider:
                                    if provider not in self.provider_index:
                                        self.provider_index[provider] = []
                                    self.provider_index[provider].append({
                                        'domain': domain,
                                        'env': env,
                                        'type': resource_type,
                                        'ref': config['ref']
                                    })
    
    def resolve(self, domain: str, environment: str, 
                resource_type: str = 'compute') -> ResolvedResource:
        """
        Resolve a logical domain to physical resource
        
        Args:
            domain: Logical service name (e.g., 'galileo_notifications')
            environment: Environment (e.g., 'prod', 'staging')
            resource_type: Type of resource (e.g., 'compute', 'database')
        
        Returns:
            ResolvedResource with all necessary information
        
        Raises:
            ValueError: If domain/environment/resource not found
        """
        
        # Check if domain exists
        if domain not in self.domains:
            raise ValueError(f"Domain '{domain}' not found. Available: {list(self.domains.keys())}")
        
        # Check if environment exists for domain
        if environment not in self.domains[domain]:
            available_envs = list(self.domains[domain].keys())
            raise ValueError(f"Environment '{environment}' not found for {domain}. Available: {available_envs}")
        
        # Check if resource type exists
        env_config = self.domains[domain][environment]
        if resource_type not in env_config:
            available_types = list(env_config.keys())
            raise ValueError(f"Resource type '{resource_type}' not found for {domain}/{environment}. Available: {available_types}")
        
        # Get resource configuration
        resource_config = env_config[resource_type]
        
        # Handle multiple refs (like multiple VMs)
        refs = resource_config.get('refs') or [resource_config.get('ref')]
        if not refs[0]:
            raise ValueError(f"No ref found for {domain}/{environment}/{resource_type}")
        
        # Build resolved resource
        resolved = ResolvedResource(
            domain=domain,
            environment=environment,
            resource_type=resource_type,
            provider=resource_config.get('provider'),
            kind=resource_config.get('kind'),
            ref=refs[0] if len(refs) == 1 else refs,
            region=resource_config.get('region'),
            account=resource_config.get('account'),
            resource_group=resource_config.get('resource_group'),
            subscription=resource_config.get('subscription'),
            project=resource_config.get('project'),
            metadata=resource_config.get('metadata', {})
        )
        
        # Add provider-specific defaults
        if resolved.provider in self.providers:
            provider_config = self.providers[resolved.provider]
            
            # Add default region if not specified
            if not resolved.region and 'default_region' in provider_config:
                resolved.region = provider_config['default_region']
            
            # Add default account/subscription if not specified
            if resolved.provider == 'aws' and not resolved.account:
                if environment in provider_config.get('accounts', {}):
                    resolved.account = provider_config['accounts'][environment]
            
            elif resolved.provider == 'azure' and not resolved.subscription:
                if environment in provider_config.get('subscriptions', {}):
                    resolved.subscription = provider_config['subscriptions'][environment]
            
            elif resolved.provider == 'gcp' and not resolved.project:
                if environment in provider_config.get('projects', {}):
                    resolved.project = provider_config['projects'][environment]
        
        return resolved
    
    def resolve_by_ref(self, provider: str, ref: str) -> Optional[Dict[str, str]]:
        """
        Reverse lookup: find domain/environment by provider and ref
        
        Args:
            provider: Provider name (e.g., 'aws')
            ref: Resource reference/ID
        
        Returns:
            Dict with domain, environment, resource_type or None if not found
        """
        key = (provider, ref)
        return self.resource_index.get(key)
    
    def list_domains(self) -> List[str]:
        """List all available domains"""
        return list(self.domains.keys())
    
    def list_environments(self, domain: str) -> List[str]:
        """List environments for a domain"""
        if domain not in self.domains:
            return []
        return list(self.domains[domain].keys())
    
    def list_resources(self, domain: str, environment: str) -> List[str]:
        """List resource types for a domain/environment"""
        if domain not in self.domains:
            return []
        if environment not in self.domains[domain]:
            return []
        return list(self.domains[domain][environment].keys())
    
    def get_all_resources_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all resources managed by a specific provider"""
        return self.provider_index.get(provider, [])
    
    def to_compute_ref(self, resolved: ResolvedResource) -> ComputeRef:
        """Convert ResolvedResource to ComputeRef for provider operations"""
        ref = ComputeRef(
            provider=resolved.provider,
            kind=resolved.kind,
            ref=resolved.ref if isinstance(resolved.ref, str) else resolved.ref[0],
            region=resolved.region,
            resource_group=resolved.resource_group,
            project=resolved.project
        )
        # Add account information if available
        if hasattr(resolved, 'account') and resolved.account:
            ref.account = resolved.account
        return ref
    
    def get_policy_for_operation(self, environment: str, operation: str) -> Dict[str, Any]:
        """Get policy rules for a specific operation in an environment"""
        if not self.policies:
            return {}
        
        env_policies = self.policies.get('environments', {}).get(environment, {})
        operation_policies = self.policies.get('operations', {}).get(operation, {})
        
        # Merge environment and operation policies
        return {**operation_policies, **env_policies}
    
    def requires_confirmation(self, environment: str, operation: str) -> bool:
        """Check if an operation requires confirmation in an environment"""
        policy = self.get_policy_for_operation(environment, operation)
        
        if policy.get('confirmations_required'):
            confirmation_ops = policy.get('confirmation_operations', [])
            return operation in confirmation_ops or not confirmation_ops
        
        return False
    
    def is_operation_allowed(self, environment: str, operation: str, mode: str = 'operator') -> bool:
        """Check if an operation is allowed based on environment and mode"""
        if not self.policies:
            return True
        
        # Get operation mode policies
        mode_config = self.policies.get('operation_modes', {}).get(mode, {})
        allowed_verbs = mode_config.get('allowed_verbs', [])
        denied_verbs = mode_config.get('denied_verbs', [])
        
        # Check if operation is explicitly denied
        if operation in denied_verbs:
            return False
        
        # Check if operation is in allowed list (or all allowed)
        if allowed_verbs == 'all' or operation in allowed_verbs:
            # Also check environment restrictions
            env_config = self.policies.get('environments', {}).get(environment, {})
            env_allowed = env_config.get('allowed_operations', 'all')
            
            if env_allowed == 'all':
                return True
            return operation in env_allowed
        
        return False
