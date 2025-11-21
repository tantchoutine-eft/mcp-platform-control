"""
Guardrails Manager for Platform Control Plane
Implements safety checks and confirmation requirements
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class GuardrailsManager:
    """Manages operational guardrails and safety checks"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.policies = self._load_policies()
        self.pending_confirmations = {}
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load policies configuration"""
        policies_file = self.config_path / "policies.yml"
        if policies_file.exists():
            with open(policies_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _generate_confirmation_token(self) -> str:
        """Generate a confirmation token"""
        token_config = self.policies.get('confirmations', {}).get('token', {})
        token_type = token_config.get('type', 'alphanumeric')
        length = token_config.get('length', 6)
        
        if token_type == 'word-based':
            words = ['ALPHA', 'BRAVO', 'CHARLIE', 'DELTA', 'ECHO', 'FOXTROT']
            return random.choice(words)
        else:
            chars = string.ascii_uppercase + string.digits
            token = ''.join(random.choice(chars) for _ in range(length))
            # Format as specified
            if length == 6:
                return f"{token[:3]}-{token[3:]}"
            return token
    
    def _requires_confirmation(self, environment: str, operation: str) -> bool:
        """Check if operation requires confirmation"""
        env_config = self.policies.get('environments', {}).get(environment, {})
        
        if env_config.get('confirmations_required'):
            confirm_ops = env_config.get('confirmation_operations', [])
            return operation in confirm_ops
        
        return False
    
    async def check_scale_operation(self, domain: str, environment: str, 
                                   target_capacity: int) -> Dict[str, Any]:
        """Check if scale operation is allowed"""
        
        # Get environment policies
        env_config = self.policies.get('environments', {}).get(environment, {})
        guardrails = self.policies.get('guardrails', {}).get('scaling', {})
        
        # Check max size
        max_size = env_config.get('max_scale_size', guardrails.get('max_instances', {}).get('default', 100))
        if target_capacity > max_size:
            return {
                'allowed': False,
                'reason': f"Target capacity {target_capacity} exceeds maximum {max_size} for {environment}"
            }
        
        # Check min size
        min_size = guardrails.get('min_instances', {}).get(environment, 1)
        if target_capacity < min_size:
            return {
                'allowed': False,
                'reason': f"Target capacity {target_capacity} below minimum {min_size} for {environment}"
            }
        
        # Check if confirmation required
        if self._requires_confirmation(environment, 'scale'):
            token = self._generate_confirmation_token()
            self.pending_confirmations[token] = {
                'operation': 'scale',
                'domain': domain,
                'environment': environment,
                'details': {'target_capacity': target_capacity},
                'expires': datetime.now() + timedelta(seconds=300)
            }
            
            return {
                'allowed': False,
                'requires_confirmation': True,
                'token': token,
                'reason': f"Scaling {domain} in {environment} requires confirmation. Enter token: {token}"
            }
        
        return {'allowed': True}
    
    async def check_restart_operation(self, domain: str, environment: str) -> Dict[str, Any]:
        """Check if restart operation is allowed"""
        
        if self._requires_confirmation(environment, 'restart'):
            token = self._generate_confirmation_token()
            self.pending_confirmations[token] = {
                'operation': 'restart',
                'domain': domain,
                'environment': environment,
                'expires': datetime.now() + timedelta(seconds=300)
            }
            
            return {
                'allowed': False,
                'requires_confirmation': True,
                'token': token,
                'reason': f"Restarting {domain} in {environment} requires confirmation. Enter token: {token}"
            }
        
        return {'allowed': True}
    
    async def check_deploy_operation(self, domain: str, environment: str, 
                                    version: str) -> Dict[str, Any]:
        """Check if deploy operation is allowed"""
        
        env_config = self.policies.get('environments', {}).get(environment, {})
        deployment_config = env_config.get('deployment_restrictions', {})
        
        # Check blackout windows
        blackout_windows = deployment_config.get('blackout_windows', [])
        current_time = datetime.now()
        
        for window in blackout_windows:
            # Parse blackout window (simplified - would need proper parsing)
            # This is a placeholder - real implementation would parse day/time properly
            if 'Friday' in window.get('start', '') and current_time.weekday() >= 4:
                return {
                    'allowed': False,
                    'reason': f"Deployments not allowed during blackout window"
                }
        
        # Check if approval required
        if deployment_config.get('approval_required'):
            # In real implementation, would check for approval
            pass
        
        # Check if confirmation required
        if self._requires_confirmation(environment, 'deploy'):
            token = self._generate_confirmation_token()
            self.pending_confirmations[token] = {
                'operation': 'deploy',
                'domain': domain,
                'environment': environment,
                'details': {'version': version},
                'expires': datetime.now() + timedelta(seconds=300)
            }
            
            return {
                'allowed': False,
                'requires_confirmation': True,
                'token': token,
                'reason': f"Deploying {version} to {domain} in {environment} requires confirmation. Enter token: {token}"
            }
        
        return {'allowed': True}
    
    async def validate_confirmation(self, token: str) -> bool:
        """Validate a confirmation token"""
        if token not in self.pending_confirmations:
            return False
        
        confirmation = self.pending_confirmations[token]
        
        # Check expiry
        if datetime.now() > confirmation['expires']:
            del self.pending_confirmations[token]
            return False
        
        # Token is valid, remove it (single use)
        del self.pending_confirmations[token]
        return True
    
    async def check_isolation_operation(self, hostname: str) -> Dict[str, Any]:
        """Check if endpoint isolation is allowed"""
        
        guardrails = self.policies.get('guardrails', {}).get('security', {})
        
        # Check max endpoints to isolate
        max_isolate = guardrails.get('max_endpoints_isolate', 10)
        # In real implementation, would check current isolated count
        
        # Always require confirmation for isolation
        token = self._generate_confirmation_token()
        self.pending_confirmations[token] = {
            'operation': 'isolate_endpoint',
            'hostname': hostname,
            'expires': datetime.now() + timedelta(seconds=300)
        }
        
        return {
            'allowed': False,
            'requires_confirmation': True,
            'token': token,
            'reason': f"🔒 Isolating {hostname} will block user access! Enter token to confirm: {token}"
        }
