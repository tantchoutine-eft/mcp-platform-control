"""
Audit Logger for Platform Control Plane
Tracks all operations for compliance and debugging
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class AuditLogger:
    """Comprehensive audit logging for all platform operations"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.policies = self._load_policies()
        self.audit_config = self.policies.get('audit', {})
        
        # Set up audit log path
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Current session info
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.current_user = "cursor-user"  # Would be set by authentication
        
        # Audit log file
        self.audit_file = self.log_dir / f"audit-{self.session_id}.jsonl"
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load policies configuration"""
        policies_file = self.config_path / "policies.yml"
        if policies_file.exists():
            with open(policies_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def log_operation(self, operation: str, **kwargs) -> None:
        """Log an operation to audit trail"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'user': self.current_user,
            'operation': operation,
            'parameters': kwargs,
            'status': 'initiated'
        }
        
        # Write to file
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # In production, would also:
        # - Send to S3/Blob storage
        # - Stream to Kinesis/Event Hub
        # - Index in Elasticsearch
    
    def log_success(self, operation: str, result: Any = None, **kwargs) -> None:
        """Log successful operation completion"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'user': self.current_user,
            'operation': operation,
            'parameters': kwargs,
            'status': 'success',
            'result_summary': self._summarize_result(result)
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_error(self, operation: str, error: str, **kwargs) -> None:
        """Log operation failure"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'user': self.current_user,
            'operation': operation,
            'parameters': kwargs,
            'status': 'failed',
            'error': str(error)
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Check if this should trigger alerts
        self._check_alert_conditions(operation, error)
    
    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]) -> None:
        """Log security-related events"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'user': self.current_user,
            'event_type': 'security',
            'security_event': event_type,
            'severity': severity,
            'details': details
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # High severity events should trigger immediate alerts
        if severity in ['critical', 'high']:
            asyncio.create_task(self._send_security_alert(event_type, severity, details))
    
    def _summarize_result(self, result: Any) -> Dict[str, Any]:
        """Create summary of operation result for audit log"""
        if result is None:
            return {}
        
        if isinstance(result, dict):
            # Extract key fields without sensitive data
            summary = {}
            safe_fields = ['success', 'status', 'count', 'name', 'domain', 'environment']
            for field in safe_fields:
                if field in result:
                    summary[field] = result[field]
            return summary
        
        return {'type': type(result).__name__}
    
    def _check_alert_conditions(self, operation: str, error: str) -> None:
        """Check if error conditions should trigger alerts"""
        
        alert_config = self.audit_config.get('alerts', {})
        
        # Check for repeated failures
        # In production, would track failure counts in memory/Redis
        
        # Check for critical operations failing
        critical_operations = ['isolate_endpoint', 'failover', 'deploy']
        if operation in critical_operations:
            asyncio.create_task(self._send_operational_alert(operation, error))
    
    async def _send_security_alert(self, event_type: str, severity: str, details: Dict[str, Any]) -> None:
        """Send security alert to configured channels"""
        
        # In production, would integrate with:
        # - Slack webhook
        # - PagerDuty
        # - Email
        # - SIEM system
        
        print(f"🚨 SECURITY ALERT: {event_type} - {severity}")
        print(f"   Details: {details}")
    
    async def _send_operational_alert(self, operation: str, error: str) -> None:
        """Send operational alert for critical failures"""
        
        print(f"⚠️ OPERATIONAL ALERT: {operation} failed")
        print(f"   Error: {error}")
    
    def get_recent_operations(self, minutes: int = 60, 
                             operation_filter: Optional[str] = None) -> list:
        """Retrieve recent operations from audit log"""
        
        operations = []
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        if not self.audit_file.exists():
            return operations
        
        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                    
                    if entry_time >= cutoff_time:
                        if operation_filter is None or entry.get('operation') == operation_filter:
                            operations.append(entry)
                except:
                    continue
        
        return operations
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for audit period"""
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'operations': {
                'total': 0,
                'by_type': {},
                'by_user': {},
                'by_environment': {}
            },
            'failures': [],
            'security_events': [],
            'high_risk_operations': []
        }
        
        # Process audit logs
        # In production, would query from S3/database
        
        return report
