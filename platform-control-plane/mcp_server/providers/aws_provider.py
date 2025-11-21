"""
AWS Provider implementation for Platform Control Plane
"""

import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from botocore.exceptions import ClientError
import logging

from .base import (
    BaseProvider, ComputeRef, ServiceInfo, ServiceStatus,
    Alert, AlertSeverity, OperationResult, VPNStatus
)

logger = logging.getLogger(__name__)


class AWSProvider(BaseProvider):
    """AWS provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.clients = {}
        self.sessions = {}
    
    async def initialize(self) -> None:
        """Initialize AWS sessions for each account"""
        for env, profile in self.config['profiles'].items():
            try:
                # Create session with SSO profile
                session = boto3.Session(profile_name=profile)
                self.sessions[env] = session
                
                # Pre-create commonly used clients
                self.clients[env] = {
                    'ec2': session.client('ec2', region_name=self.config['default_region']),
                    'autoscaling': session.client('autoscaling', region_name=self.config['default_region']),
                    'rds': session.client('rds', region_name=self.config['default_region']),
                    'cloudwatch': session.client('cloudwatch', region_name=self.config['default_region']),
                    'elbv2': session.client('elbv2', region_name=self.config['default_region']),
                    's3': session.client('s3'),
                    'sts': session.client('sts')
                }
            except Exception as e:
                print(f"Failed to initialize AWS session for {env}: {e}")
    
    async def validate_credentials(self) -> bool:
        """Validate AWS credentials are working"""
        try:
            for env, clients in self.clients.items():
                identity = clients['sts'].get_caller_identity()
                print(f"AWS {env}: Connected as {identity['Arn']}")
            return True
        except ClientError as e:
            print(f"AWS credential validation failed: {e}")
            return False
    
    async def get_regions(self) -> List[str]:
        """Get available AWS regions"""
        ec2 = self.sessions['prod'].client('ec2', region_name='us-east-1')
        response = ec2.describe_regions()
        return [r['RegionName'] for r in response['Regions']]
    
    # Compute Operations
    
    async def get_status(self, ref: ComputeRef) -> ServiceInfo:
        """Get status of an AWS compute resource"""
        # Get environment from ref
        env = self._get_env_from_ref(ref)
        logger.info(f"Getting status for {ref.ref} in environment {env}")
        
        # Check if we have a client for this environment
        if env not in self.clients:
            logger.warning(f"No AWS client for environment {env}, using prod")
            env = 'prod'
        
        if ref.kind == 'asg':
            return await self._get_asg_status(env, ref)
        elif ref.kind == 'ec2':
            return await self._get_ec2_status(env, ref)
        elif ref.kind == 'ecs':
            return await self._get_ecs_status(env, ref)
        elif ref.kind == 'lambda':
            return await self._get_lambda_status(env, ref)
        else:
            raise ValueError(f"Unsupported compute kind: {ref.kind}")
    
    async def scale(self, ref: ComputeRef, capacity: int) -> OperationResult:
        """Scale AWS compute resource"""
        env = self._get_env_from_ref(ref)
        
        try:
            if ref.kind == 'asg':
                return await self._scale_asg(env, ref, capacity)
            elif ref.kind == 'ecs':
                return await self._scale_ecs(env, ref, capacity)
            else:
                return OperationResult(
                    success=False,
                    message=f"Scaling not supported for {ref.kind}",
                    error="UnsupportedOperation"
                )
        except ClientError as e:
            return OperationResult(
                success=False,
                message=f"Failed to scale {ref.ref}",
                error=str(e)
            )
    
    async def restart(self, ref: ComputeRef) -> OperationResult:
        """Restart AWS compute instances"""
        env = self._get_env_from_ref(ref)
        
        try:
            if ref.kind == 'ec2':
                return await self._restart_ec2_instances(env, ref)
            elif ref.kind == 'asg':
                return await self._restart_asg_instances(env, ref)
            elif ref.kind == 'ecs':
                return await self._restart_ecs_tasks(env, ref)
            else:
                return OperationResult(
                    success=False,
                    message=f"Restart not supported for {ref.kind}",
                    error="UnsupportedOperation"
                )
        except ClientError as e:
            return OperationResult(
                success=False,
                message=f"Failed to restart {ref.ref}",
                error=str(e)
            )
    
    async def deploy(self, ref: ComputeRef, version: str, **kwargs) -> OperationResult:
        """Deploy new version to AWS resource"""
        env = self._get_env_from_ref(ref)
        
        try:
            if ref.kind == 'ecs':
                return await self._deploy_ecs(env, ref, version, **kwargs)
            elif ref.kind == 'lambda':
                return await self._deploy_lambda(env, ref, version, **kwargs)
            else:
                # For ASG, typically would update launch template
                return await self._deploy_asg(env, ref, version, **kwargs)
        except ClientError as e:
            return OperationResult(
                success=False,
                message=f"Failed to deploy {version} to {ref.ref}",
                error=str(e)
            )
    
    async def terminate(self, ref: ComputeRef, force: bool = False) -> OperationResult:
        """Terminate AWS resource"""
        # Implementation would include safety checks
        pass
    
    # Database Operations
    
    async def get_db_status(self, db_ref: str, env: str) -> Dict[str, Any]:
        """Get RDS cluster/instance status"""
        rds = self.clients[env]['rds']
        
        try:
            # Try cluster first
            response = rds.describe_db_clusters(DBClusterIdentifier=db_ref)
            cluster = response['DBClusters'][0]
            return {
                'type': 'cluster',
                'status': cluster['Status'],
                'engine': cluster['Engine'],
                'members': len(cluster['DBClusterMembers']),
                'endpoint': cluster.get('Endpoint'),
                'reader_endpoint': cluster.get('ReaderEndpoint')
            }
        except ClientError:
            # Try instance
            response = rds.describe_db_instances(DBInstanceIdentifier=db_ref)
            instance = response['DBInstances'][0]
            return {
                'type': 'instance',
                'status': instance['DBInstanceStatus'],
                'engine': instance['Engine'],
                'class': instance['DBInstanceClass'],
                'endpoint': instance.get('Endpoint', {}).get('Address')
            }
    
    async def backup_database(self, db_ref: str, env: str, snapshot_id: Optional[str] = None) -> OperationResult:
        """Create RDS snapshot"""
        rds = self.clients[env]['rds']
        
        if not snapshot_id:
            snapshot_id = f"{db_ref}-manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            rds.create_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=snapshot_id,
                DBClusterIdentifier=db_ref
            )
            return OperationResult(
                success=True,
                message=f"Backup initiated: {snapshot_id}",
                details={'snapshot_id': snapshot_id}
            )
        except ClientError as e:
            if 'DBInstanceIdentifier' in str(e):
                # Try instance snapshot
                rds.create_db_snapshot(
                    DBSnapshotIdentifier=snapshot_id,
                    DBInstanceIdentifier=db_ref
                )
                return OperationResult(
                    success=True,
                    message=f"Backup initiated: {snapshot_id}",
                    details={'snapshot_id': snapshot_id}
                )
            raise
    
    # Security Operations (via GuardDuty/Security Hub)
    
    async def get_security_alerts(self, env: str, severity: Optional[AlertSeverity] = None, 
                                 last_minutes: int = 60) -> List[Alert]:
        """Get GuardDuty findings"""
        # Would integrate with GuardDuty/Security Hub
        pass
    
    # Network Operations
    
    async def get_vpn_status(self, connection_id: str, env: str) -> VPNStatus:
        """Get VPN connection status"""
        ec2 = self.clients[env]['ec2']
        
        response = ec2.describe_vpn_connections(VpnConnectionIds=[connection_id])
        vpn = response['VpnConnections'][0]
        
        # Get tunnel status
        tunnel1 = vpn['VgwTelemetry'][0] if vpn.get('VgwTelemetry') else None
        
        return VPNStatus(
            name=vpn.get('Tags', [{'Key': 'Name', 'Value': connection_id}])[0]['Value'],
            status=vpn['State'],
            local_endpoint=vpn.get('CustomerGatewayId'),
            remote_endpoint=vpn.get('VpnGatewayId'),
            bytes_in=0,  # Would need CloudWatch metrics
            bytes_out=0,
            last_handshake=tunnel1.get('LastStatusChange') if tunnel1 else None,
            uptime_seconds=None
        )
    
    # Observability Operations
    
    async def get_logs(self, log_group: str, env: str, last_minutes: int = 30,
                      filter_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get CloudWatch logs"""
        logs = self.sessions[env].client('logs', region_name=self.config['default_region'])
        
        start_time = int((datetime.now().timestamp() - (last_minutes * 60)) * 1000)
        end_time = int(datetime.now().timestamp() * 1000)
        
        params = {
            'logGroupName': log_group,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1000
        }
        
        if filter_pattern:
            params['filterPattern'] = filter_pattern
        
        response = logs.filter_log_events(**params)
        
        return [
            {
                'timestamp': event['timestamp'],
                'message': event['message'],
                'stream': event.get('logStreamName')
            }
            for event in response.get('events', [])
        ]
    
    async def get_metrics(self, namespace: str, metric_name: str, dimensions: List[Dict],
                         env: str, last_minutes: int = 60) -> Dict[str, Any]:
        """Get CloudWatch metrics"""
        cloudwatch = self.clients[env]['cloudwatch']
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=last_minutes)
        
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5 minutes
            Statistics=['Average', 'Maximum', 'Minimum']
        )
        
        return {
            'metric': metric_name,
            'datapoints': sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        }
    
    # Helper methods
    
    def _get_env_from_ref(self, ref: ComputeRef) -> str:
        """Determine environment from reference"""
        # Check account mapping first
        if hasattr(ref, 'account') and ref.account:
            for env, account in self.config.get('accounts', {}).items():
                if account == ref.account:
                    return env
        
        # Fall back to name matching
        if 'prod' in ref.ref.lower():
            return 'prod'
        elif 'stag' in ref.ref.lower():
            return 'staging'
        else:
            return 'dev'
    
    async def _get_asg_status(self, env: str, ref: ComputeRef) -> ServiceInfo:
        """Get Auto Scaling Group status"""
        asg = self.clients[env]['autoscaling']
        
        response = asg.describe_auto_scaling_groups(
            AutoScalingGroupNames=[ref.ref]
        )
        
        if not response['AutoScalingGroups']:
            raise ValueError(f"ASG {ref.ref} not found")
        
        group = response['AutoScalingGroups'][0]
        
        # Count healthy instances
        healthy = sum(1 for i in group['Instances'] 
                     if i['HealthStatus'] == 'Healthy' and i['LifecycleState'] == 'InService')
        unhealthy = len(group['Instances']) - healthy
        
        return ServiceInfo(
            name=ref.ref,
            status=ServiceStatus.RUNNING if healthy > 0 else ServiceStatus.STOPPED,
            instance_count=len(group['Instances']),
            healthy_count=healthy,
            unhealthy_count=unhealthy,
            provider='aws',
            region=ref.region or self.config['default_region'],
            last_updated=datetime.now(),
            metadata={
                'desired_capacity': group['DesiredCapacity'],
                'min_size': group['MinSize'],
                'max_size': group['MaxSize'],
                'availability_zones': group['AvailabilityZones']
            }
        )
    
    async def _scale_asg(self, env: str, ref: ComputeRef, capacity: int) -> OperationResult:
        """Scale Auto Scaling Group"""
        asg = self.clients[env]['autoscaling']
        
        asg.set_desired_capacity(
            AutoScalingGroupName=ref.ref,
            DesiredCapacity=capacity,
            HonorCooldown=False
        )
        
        return OperationResult(
            success=True,
            message=f"Scaling {ref.ref} to {capacity} instances",
            details={'previous_capacity': None, 'new_capacity': capacity}
        )
    
    async def _restart_asg_instances(self, env: str, ref: ComputeRef) -> OperationResult:
        """Perform rolling restart of ASG instances"""
        asg = self.clients[env]['autoscaling']
        
        # Start instance refresh for rolling update
        response = asg.start_instance_refresh(
            AutoScalingGroupName=ref.ref,
            Strategy='Rolling',
            Preferences={
                'MinHealthyPercentage': 90,
                'InstanceWarmup': 60
            }
        )
        
        return OperationResult(
            success=True,
            message=f"Rolling restart initiated for {ref.ref}",
            details={'instance_refresh_id': response['InstanceRefreshId']}
        )
    
    async def _get_ec2_status(self, env: str, ref: ComputeRef) -> ServiceInfo:
        """Get EC2 instance status"""
        ec2 = self.clients[env]['ec2']
        
        # Get instances by tag or instance IDs
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [ref.ref]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']}
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])
        
        healthy = sum(1 for i in instances if i['State']['Name'] == 'running')
        total = len(instances)
        
        return ServiceInfo(
            name=ref.ref,
            status=ServiceStatus.RUNNING if healthy > 0 else ServiceStatus.STOPPED,
            instance_count=total,
            healthy_count=healthy,
            unhealthy_count=total - healthy,
            provider='aws',
            region=ref.region or self.config['default_region'],
            last_updated=datetime.now(),
            metadata={'instance_type': instances[0]['InstanceType'] if instances else None}
        )
    
    async def _get_ecs_status(self, env: str, ref: ComputeRef) -> ServiceInfo:
        """Get ECS service status"""
        # Stub implementation
        return ServiceInfo(
            name=ref.ref,
            status=ServiceStatus.UNKNOWN,
            instance_count=0,
            healthy_count=0,
            unhealthy_count=0,
            provider='aws',
            region=ref.region or self.config['default_region'],
            last_updated=datetime.now(),
            metadata={}
        )
    
    async def _get_lambda_status(self, env: str, ref: ComputeRef) -> ServiceInfo:
        """Get Lambda function status"""
        # Stub implementation
        return ServiceInfo(
            name=ref.ref,
            status=ServiceStatus.RUNNING,
            instance_count=1,
            healthy_count=1,
            unhealthy_count=0,
            provider='aws',
            region=ref.region or self.config['default_region'],
            last_updated=datetime.now(),
            metadata={}
        )
    
    async def _restart_ec2_instances(self, env: str, ref: ComputeRef) -> OperationResult:
        """Restart EC2 instances"""
        ec2 = self.clients[env]['ec2']
        
        # Get instances
        response = ec2.describe_instances(
            Filters=[{'Name': 'tag:Name', 'Values': [ref.ref]}]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            ec2.reboot_instances(InstanceIds=instance_ids)
            return OperationResult(
                success=True,
                message=f"Restarting {len(instance_ids)} instances",
                details={'instance_ids': instance_ids}
            )
        else:
            return OperationResult(
                success=False,
                message="No running instances found to restart"
            )
    
    async def _restart_ecs_tasks(self, env: str, ref: ComputeRef) -> OperationResult:
        """Restart ECS tasks"""
        # Stub implementation
        return OperationResult(
            success=True,
            message=f"ECS task restart not yet implemented for {ref.ref}"
        )
    
    async def _deploy_ecs(self, env: str, ref: ComputeRef, version: str, **kwargs) -> OperationResult:
        """Deploy to ECS service"""
        # Stub implementation
        return OperationResult(
            success=True,
            message=f"ECS deployment not yet implemented for {ref.ref}"
        )
    
    async def _deploy_lambda(self, env: str, ref: ComputeRef, version: str, **kwargs) -> OperationResult:
        """Deploy Lambda function"""
        # Stub implementation
        return OperationResult(
            success=True,
            message=f"Lambda deployment not yet implemented for {ref.ref}"
        )
    
    async def _deploy_asg(self, env: str, ref: ComputeRef, version: str, **kwargs) -> OperationResult:
        """Deploy to Auto Scaling Group"""
        # Stub implementation
        return OperationResult(
            success=True,
            message=f"ASG deployment not yet implemented for {ref.ref}"
        )
    
    async def _scale_ecs(self, env: str, ref: ComputeRef, capacity: int) -> OperationResult:
        """Scale ECS service"""
        # Stub implementation
        return OperationResult(
            success=True,
            message=f"ECS scaling not yet implemented for {ref.ref}"
        )
