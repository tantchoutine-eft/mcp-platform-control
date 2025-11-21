"""
Base provider interfaces for the Platform Control Plane.
All provider implementations must conform to these protocols.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Optional, Dict, List, Any, Literal
from datetime import datetime
from enum import Enum


class ServiceStatus(Enum):
    """Canonical service states across all providers"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    FAILED = "failed"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Standardized alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComputeRef:
    """Reference to a compute resource"""
    provider: str
    kind: str  # asg, vmss, mig, etc.
    ref: str   # actual resource identifier
    region: Optional[str] = None
    account: Optional[str] = None  # AWS account ID
    resource_group: Optional[str] = None  # For Azure
    project: Optional[str] = None  # For GCP


@dataclass
class ServiceInfo:
    """Standardized service information"""
    name: str
    status: ServiceStatus
    instance_count: int
    healthy_count: int
    unhealthy_count: int
    provider: str
    region: str
    last_updated: datetime
    metadata: Dict[str, Any]


@dataclass
class Alert:
    """Standardized alert format"""
    id: str
    title: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    description: str
    affected_resources: List[str]
    status: str  # active, acknowledged, resolved
    metadata: Dict[str, Any]


@dataclass
class VPNStatus:
    """Standardized VPN tunnel status"""
    name: str
    status: str  # up, down, connecting
    local_endpoint: str
    remote_endpoint: str
    bytes_in: int
    bytes_out: int
    last_handshake: Optional[datetime]
    uptime_seconds: Optional[int]


@dataclass
class OperationResult:
    """Result of any operation"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Provider Interfaces (Protocols)

class ComputeProvider(Protocol):
    """Interface for compute operations"""
    
    @abstractmethod
    async def get_status(self, ref: ComputeRef) -> ServiceInfo:
        """Get current status of a compute resource"""
        ...
    
    @abstractmethod
    async def scale(self, ref: ComputeRef, capacity: int) -> OperationResult:
        """Scale compute resource to specified capacity"""
        ...
    
    @abstractmethod
    async def restart(self, ref: ComputeRef) -> OperationResult:
        """Restart/reboot compute instances"""
        ...
    
    @abstractmethod
    async def deploy(self, ref: ComputeRef, version: str, **kwargs) -> OperationResult:
        """Deploy new version to compute resource"""
        ...
    
    @abstractmethod
    async def terminate(self, ref: ComputeRef, force: bool = False) -> OperationResult:
        """Terminate compute resource"""
        ...


class SecurityProvider(Protocol):
    """Interface for security operations"""
    
    @abstractmethod
    async def get_alerts(
        self, 
        severity: Optional[AlertSeverity] = None,
        last_minutes: int = 60,
        limit: int = 100
    ) -> List[Alert]:
        """Get security alerts"""
        ...
    
    @abstractmethod
    async def isolate_endpoint(self, hostname: str) -> OperationResult:
        """Isolate an endpoint from network"""
        ...
    
    @abstractmethod
    async def release_endpoint(self, hostname: str) -> OperationResult:
        """Release an endpoint from isolation"""
        ...
    
    @abstractmethod
    async def scan_endpoint(self, hostname: str, scan_type: str = "quick") -> OperationResult:
        """Initiate security scan on endpoint"""
        ...


class NetworkProvider(Protocol):
    """Interface for network operations"""
    
    @abstractmethod
    async def get_vpn_status(self, tunnel_name: str) -> VPNStatus:
        """Get VPN tunnel status"""
        ...
    
    @abstractmethod
    async def restart_vpn(self, tunnel_name: str) -> OperationResult:
        """Restart VPN tunnel"""
        ...
    
    @abstractmethod
    async def update_firewall_rule(
        self, 
        rule_name: str, 
        enabled: bool,
        **kwargs
    ) -> OperationResult:
        """Enable/disable firewall rule"""
        ...
    
    @abstractmethod
    async def test_connectivity(
        self, 
        source: str, 
        destination: str,
        port: Optional[int] = None
    ) -> OperationResult:
        """Test network connectivity"""
        ...


class DatabaseProvider(Protocol):
    """Interface for database operations"""
    
    @abstractmethod
    async def get_status(self, db_ref: str) -> Dict[str, Any]:
        """Get database cluster status"""
        ...
    
    @abstractmethod
    async def backup(self, db_ref: str, backup_name: Optional[str] = None) -> OperationResult:
        """Initiate database backup"""
        ...
    
    @abstractmethod
    async def restore(self, db_ref: str, backup_id: str) -> OperationResult:
        """Restore database from backup"""
        ...
    
    @abstractmethod
    async def failover(self, db_ref: str, target: Optional[str] = None) -> OperationResult:
        """Initiate database failover"""
        ...
    
    @abstractmethod
    async def resize(self, db_ref: str, instance_class: str) -> OperationResult:
        """Resize database instance"""
        ...


class ObservabilityProvider(Protocol):
    """Interface for observability operations"""
    
    @abstractmethod
    async def get_logs(
        self,
        service: str,
        last_minutes: int = 30,
        severity: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve logs"""
        ...
    
    @abstractmethod
    async def get_metrics(
        self,
        service: str,
        metric_names: List[str],
        last_minutes: int = 60
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve metrics"""
        ...
    
    @abstractmethod
    async def create_alert(
        self,
        name: str,
        condition: str,
        threshold: float,
        **kwargs
    ) -> OperationResult:
        """Create monitoring alert"""
        ...


class BaseProvider(ABC):
    """Base class for all providers with common functionality"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider connections"""
        ...
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate provider credentials are working"""
        ...
    
    @abstractmethod
    async def get_regions(self) -> List[str]:
        """Get available regions/locations for this provider"""
        ...
    
    def _log_operation(self, operation: str, params: Dict[str, Any], result: Any) -> None:
        """Log operation for audit trail"""
        # This will be implemented by the audit module
        pass
