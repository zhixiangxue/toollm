import psutil
import signal
import os
from typing import Dict, Any, List, Optional


class Process:
    """
    ⚠️ WARNING: For development/testing only, NOT for production use
    ⚠️ WARNING: Process operations can affect system stability
    ⚠️ WARNING: Use with caution, especially kill operations
    
    Process management toolkit - Monitor and control system processes
    
    Design principles:
    - Minimal API (list, info, kill)
    - Cross-platform compatible
    - Structured return values
    - Safe defaults
    """
    
    def __init__(self, allow_system_processes: bool = False):
        """
        Args:
            allow_system_processes: Allow operations on system processes (default: False)
        """
        self.allow_system_processes = allow_system_processes
    
    def list(self, filter: Optional[str] = None, sort_by: str = 'cpu') -> Dict[str, Any]:
        """
        List running processes
        
        Args:
            filter: Filter by process name (substring match, case-insensitive)
            sort_by: Sort by 'cpu', 'memory', 'pid', or 'name' (default: 'cpu')
            
        Returns:
            {
                'success': bool,
                'processes': List[Dict],  # List of process info
                'count': int,             # Number of processes
                'error': str
            }
        """
        if sort_by not in ['cpu', 'memory', 'pid', 'name']:
            return {
                'success': False,
                'error': f"Invalid sort_by: {sort_by}. Must be 'cpu', 'memory', 'pid', or 'name'"
            }
        
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
                try:
                    pinfo = proc.info
                    
                    # Apply filter
                    if filter and filter.lower() not in pinfo['name'].lower():
                        continue
                    
                    # Get additional info
                    with proc.oneshot():
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        memory_info = proc.memory_info()
                        create_time = proc.create_time()
                    
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'username': pinfo['username'],
                        'status': pinfo['status'],
                        'cpu_percent': round(cpu_percent, 2),
                        'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                        'create_time': create_time
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort processes
            sort_key_map = {
                'cpu': lambda x: x['cpu_percent'],
                'memory': lambda x: x['memory_mb'],
                'pid': lambda x: x['pid'],
                'name': lambda x: x['name'].lower()
            }
            
            processes.sort(key=sort_key_map[sort_by], reverse=(sort_by in ['cpu', 'memory']))
            
            return {
                'success': True,
                'processes': processes,
                'count': len(processes)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'List error: {str(e)}'
            }
    
    def info(self, pid: int) -> Dict[str, Any]:
        """
        Get detailed information about a process
        
        Args:
            pid: Process ID
            
        Returns:
            {
                'success': bool,
                'pid': int,
                'name': str,
                'status': str,
                'username': str,
                'cpu_percent': float,
                'memory_mb': float,
                'num_threads': int,
                'cmdline': List[str],    # Command line arguments
                'cwd': str,              # Current working directory
                'create_time': float,    # Process start time
                'error': str
            }
        """
        try:
            proc = psutil.Process(pid)
            
            with proc.oneshot():
                info = {
                    'success': True,
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'username': proc.username(),
                    'cpu_percent': round(proc.cpu_percent(interval=0.1), 2),
                    'memory_mb': round(proc.memory_info().rss / 1024 / 1024, 2),
                    'num_threads': proc.num_threads(),
                    'cmdline': proc.cmdline(),
                    'create_time': proc.create_time()
                }
                
                # Try to get cwd (may fail for system processes)
                try:
                    info['cwd'] = proc.cwd()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    info['cwd'] = 'N/A'
            
            return info
            
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'error': f'Process {pid} not found'
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'error': f'Access denied to process {pid}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Info error: {str(e)}'
            }
    
    def kill(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Terminate a process
        
        Args:
            pid: Process ID
            force: Force kill (SIGKILL) instead of graceful termination (default: False)
            
        Returns:
            {
                'success': bool,
                'pid': int,
                'name': str,
                'error': str
            }
        """
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            
            # Safety check: prevent killing system processes
            if not self.allow_system_processes:
                if self._is_system_process(proc):
                    return {
                        'success': False,
                        'error': f'Blocked: {name} appears to be a system process. Set allow_system_processes=True to override.'
                    }
            
            # Terminate process
            if force:
                proc.kill()  # SIGKILL
            else:
                proc.terminate()  # SIGTERM
            
            # Wait for process to terminate
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                if not force:
                    return {
                        'success': False,
                        'error': f'Process {pid} did not terminate gracefully. Use force=True to force kill.'
                    }
            
            return {
                'success': True,
                'pid': pid,
                'name': name
            }
            
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'error': f'Process {pid} not found'
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'error': f'Access denied to process {pid}. May require elevated privileges.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Kill error: {str(e)}'
            }
    
    def _is_system_process(self, proc: psutil.Process) -> bool:
        """Check if process is a system process"""
        try:
            # Common system process indicators
            name = proc.name().lower()
            system_names = [
                'system', 'kernel', 'init', 'systemd', 'launchd',
                'csrss', 'smss', 'wininit', 'services', 'lsass',
                'svchost', 'explorer'
            ]
            
            # Check by name
            if any(sys_name in name for sys_name in system_names):
                return True
            
            # Check by PID (0, 1, 4 are typically system)
            if proc.pid in [0, 1, 4]:
                return True
            
            # Check by username (root/SYSTEM)
            try:
                username = proc.username().lower()
                if username in ['root', 'system', 'nt authority\\system']:
                    return True
            except:
                pass
            
            return False
            
        except:
            return True  # If we can't determine, assume it's system process
    
    def __repr__(self):
        return f"<Process allow_system={self.allow_system_processes}>"


def demo():
    """Demo usage example"""
    print("=== Process Management Demo ===\n")
    
    proc_mgr = Process()
    
    # 1. List all processes sorted by CPU
    print("1. List top 10 processes by CPU:")
    result = proc_mgr.list(sort_by='cpu')
    if result['success']:
        print(f"   Total processes: {result['count']}")
        for p in result['processes'][:10]:
            print(f"   PID {p['pid']:6} | {p['name']:30} | CPU: {p['cpu_percent']:6.2f}% | MEM: {p['memory_mb']:8.2f}MB")
        print()
    
    # 2. Filter processes by name
    print("2. Filter processes (python):")
    result = proc_mgr.list(filter='python', sort_by='memory')
    if result['success']:
        print(f"   Found {result['count']} python processes:")
        for p in result['processes']:
            print(f"   PID {p['pid']:6} | {p['name']:30} | MEM: {p['memory_mb']:8.2f}MB")
        print()
    
    # 3. Get detailed info about current process
    print("3. Get info about current process:")
    current_pid = os.getpid()
    result = proc_mgr.info(current_pid)
    if result['success']:
        print(f"   PID: {result['pid']}")
        print(f"   Name: {result['name']}")
        print(f"   Status: {result['status']}")
        print(f"   CPU: {result['cpu_percent']}%")
        print(f"   Memory: {result['memory_mb']}MB")
        print(f"   Threads: {result['num_threads']}")
        print(f"   CWD: {result['cwd']}")
        print()
    
    # 4. Try to kill a non-existent process (safe test)
    print("4. Try to kill non-existent process:")
    result = proc_mgr.kill(999999)
    print(f"   Result: {result}\n")
    
    print("Demo completed.")


if __name__ == "__main__":
    demo()
