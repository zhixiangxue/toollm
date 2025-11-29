import psutil
import platform
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class System:
    """
    ⚠️ WARNING: For development/testing only, NOT for production use
    ⚠️ WARNING: System information may contain sensitive data
    
    System information toolkit - Monitor system resources and status
    
    Design principles:
    - Minimal API (info, disk, network, env)
    - Cross-platform compatible
    - Structured return values
    - Read-only operations (safe)
    """
    
    def __init__(self):
        """Initialize system monitor"""
        pass
    
    def info(self) -> Dict[str, Any]:
        """
        Get general system information
        
        Returns:
            {
                'success': bool,
                'platform': str,         # OS name (Windows/Linux/Darwin)
                'platform_version': str, # OS version
                'architecture': str,     # CPU architecture
                'hostname': str,         # Computer name
                'cpu_count': int,        # Number of CPU cores
                'cpu_percent': float,    # CPU usage percentage
                'memory_total_gb': float,# Total RAM in GB
                'memory_used_gb': float, # Used RAM in GB
                'memory_percent': float, # Memory usage percentage
                'boot_time': str,        # System boot time
                'uptime_hours': float,   # System uptime in hours
                'error': str
            }
        """
        try:
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory info
            memory = psutil.virtual_memory()
            
            # Get boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            
            return {
                'success': True,
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(logical=True),
                'cpu_percent': round(cpu_percent, 2),
                'memory_total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
                'memory_used_gb': round(memory.used / 1024 / 1024 / 1024, 2),
                'memory_percent': round(memory.percent, 2),
                'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
                'uptime_hours': round(uptime_seconds / 3600, 2)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Info error: {str(e)}'
            }
    
    def disk(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get disk usage information
        
        Args:
            path: Path to check (default: current directory)
            
        Returns:
            {
                'success': bool,
                'path': str,             # Checked path
                'total_gb': float,       # Total disk space in GB
                'used_gb': float,        # Used disk space in GB
                'free_gb': float,        # Free disk space in GB
                'percent': float,        # Usage percentage
                'mount_point': str,      # Mount point (Unix) or drive (Windows)
                'error': str
            }
        """
        try:
            target_path = path or os.getcwd()
            
            # Get disk usage
            usage = psutil.disk_usage(target_path)
            
            # Get partition info
            partition = None
            for part in psutil.disk_partitions():
                if target_path.startswith(part.mountpoint):
                    partition = part
                    break
            
            return {
                'success': True,
                'path': target_path,
                'total_gb': round(usage.total / 1024 / 1024 / 1024, 2),
                'used_gb': round(usage.used / 1024 / 1024 / 1024, 2),
                'free_gb': round(usage.free / 1024 / 1024 / 1024, 2),
                'percent': round(usage.percent, 2),
                'mount_point': partition.mountpoint if partition else 'N/A'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Disk error: {str(e)}'
            }
    
    def network(self) -> Dict[str, Any]:
        """
        Get network status and statistics
        
        Returns:
            {
                'success': bool,
                'connections': int,          # Number of active connections
                'bytes_sent_mb': float,      # Total bytes sent in MB
                'bytes_recv_mb': float,      # Total bytes received in MB
                'packets_sent': int,         # Total packets sent
                'packets_recv': int,         # Total packets received
                'interfaces': List[Dict],    # Network interface details
                'error': str
            }
        """
        try:
            # Get network IO stats
            net_io = psutil.net_io_counters()
            
            # Get network connections
            try:
                connections = len(psutil.net_connections())
            except psutil.AccessDenied:
                connections = -1  # Requires elevated privileges
            
            # Get interface info
            interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, addrs in net_if_addrs.items():
                stats = net_if_stats.get(interface_name)
                
                # Get IP addresses
                ipv4 = [addr.address for addr in addrs if addr.family == 2]
                ipv6 = [addr.address for addr in addrs if addr.family == 23 or addr.family == 30]
                
                interfaces.append({
                    'name': interface_name,
                    'ipv4': ipv4,
                    'ipv6': ipv6,
                    'is_up': stats.isup if stats else False,
                    'speed_mbps': stats.speed if stats else 0
                })
            
            return {
                'success': True,
                'connections': connections,
                'bytes_sent_mb': round(net_io.bytes_sent / 1024 / 1024, 2),
                'bytes_recv_mb': round(net_io.bytes_recv / 1024 / 1024, 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'interfaces': interfaces
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
    
    def env(self, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get environment variables
        
        Args:
            key: Specific environment variable key (default: return all)
            
        Returns:
            {
                'success': bool,
                'variables': Dict[str, str],  # All environment variables
                'value': str,                 # Specific value (if key provided)
                'count': int,                 # Number of variables
                'error': str
            }
        """
        try:
            if key:
                # Get specific variable
                value = os.environ.get(key)
                if value is None:
                    return {
                        'success': False,
                        'error': f'Environment variable "{key}" not found'
                    }
                
                return {
                    'success': True,
                    'key': key,
                    'value': value
                }
            else:
                # Get all variables
                variables = dict(os.environ)
                
                return {
                    'success': True,
                    'variables': variables,
                    'count': len(variables)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Env error: {str(e)}'
            }
    
    def __repr__(self):
        return "<System>"


def demo():
    """Demo usage example"""
    print("=== System Information Demo ===\n")
    
    sys_info = System()
    
    # 1. Get system info
    print("1. System Info:")
    result = sys_info.info()
    if result['success']:
        print(f"   Platform: {result['platform']} {result['platform_version']}")
        print(f"   Architecture: {result['architecture']}")
        print(f"   Hostname: {result['hostname']}")
        print(f"   CPU Cores: {result['cpu_count']}")
        print(f"   CPU Usage: {result['cpu_percent']}%")
        print(f"   Memory: {result['memory_used_gb']}GB / {result['memory_total_gb']}GB ({result['memory_percent']}%)")
        print(f"   Boot Time: {result['boot_time']}")
        print(f"   Uptime: {result['uptime_hours']} hours")
        print()
    
    # 2. Get disk usage
    print("2. Disk Usage:")
    result = sys_info.disk()
    if result['success']:
        print(f"   Path: {result['path']}")
        print(f"   Mount: {result['mount_point']}")
        print(f"   Total: {result['total_gb']}GB")
        print(f"   Used: {result['used_gb']}GB")
        print(f"   Free: {result['free_gb']}GB")
        print(f"   Usage: {result['percent']}%")
        print()
    
    # 3. Get network status
    print("3. Network Status:")
    result = sys_info.network()
    if result['success']:
        print(f"   Active Connections: {result['connections']}")
        print(f"   Bytes Sent: {result['bytes_sent_mb']}MB")
        print(f"   Bytes Received: {result['bytes_recv_mb']}MB")
        print(f"   Packets Sent: {result['packets_sent']}")
        print(f"   Packets Received: {result['packets_recv']}")
        print(f"   Interfaces:")
        for iface in result['interfaces']:
            if iface['is_up']:
                print(f"      {iface['name']}: {iface['ipv4']}")
        print()
    
    # 4. Get environment variable
    print("4. Environment Variables:")
    result = sys_info.env(key='PATH')
    if result['success']:
        print(f"   PATH: {result['value'][:100]}...")
        print()
    
    # 5. Count all environment variables
    result = sys_info.env()
    if result['success']:
        print(f"   Total environment variables: {result['count']}")
        print()
    
    print("Demo completed.")


if __name__ == "__main__":
    demo()
