"""
Function-style API for toollm

Provides stateless function wrappers for easy integration with AI frameworks
like LangChain, OpenAI Function Calling, etc.

All functions create temporary instances internally and return structured results.
"""

from typing import Dict, Any, Optional, List
from .cmd import CommandRunner
from .fetch import Fetch
from .file import File
from .process import Process
from .system import System
import tempfile


# ============================================================================
# Command Execution Functions
# ============================================================================

def execute_command(command: str, workdir: Optional[str] = None, 
                   timeout: int = 60, **kwargs) -> Dict[str, Any]:
    """
    Execute shell command in a sandboxed environment
    
    Args:
        command: Command to execute
        workdir: Working directory (creates temp dir if None)
        timeout: Command timeout in seconds
        **kwargs: Additional subprocess parameters
        
    Returns:
        {
            'success': bool,
            'returncode': int,
            'stdout': str,
            'stderr': str,
            'workdir': str,
            'error': str  # On failure
        }
    """
    runner = CommandRunner(workdir=workdir, timeout=timeout)
    try:
        result = runner.execute(command, **kwargs)
        return result
    finally:
        if not workdir:  # Clean up temp dir
            runner.cleanup()


def list_workdir_files(workdir: str) -> List[str]:
    """
    List files in working directory
    
    Args:
        workdir: Directory path
        
    Returns:
        List of filenames
    """
    runner = CommandRunner(workdir=workdir)
    return runner.list_files()


def read_workdir_file(workdir: str, filename: str) -> Optional[str]:
    """
    Read file content from working directory
    
    Args:
        workdir: Directory path
        filename: File name
        
    Returns:
        File content or None on error
    """
    runner = CommandRunner(workdir=workdir)
    return runner.read_file(filename)


def write_workdir_file(workdir: str, filename: str, content: str) -> bool:
    """
    Write file to working directory
    
    Args:
        workdir: Directory path
        filename: File name
        content: File content
        
    Returns:
        True on success, False on error
    """
    runner = CommandRunner(workdir=workdir)
    return runner.write_file(filename, content)


# ============================================================================
# Web Fetch Functions
# ============================================================================

def fetch_url(url: str, format: str = 'content', workdir: Optional[str] = None,
             headers: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch content from URL
    
    Args:
        url: Target URL
        format: Response format ('content', 'raw', or 'json')
        workdir: Working directory for downloads
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        {
            'success': bool,
            'content': str,
            'url': str,
            'status_code': int,
            'content_type': str,
            'error': str  # On failure
        }
    """
    temp_dir = None
    if workdir is None:
        temp_dir = tempfile.mkdtemp(prefix="fetch_")
        workdir = temp_dir
    
    try:
        fetch = Fetch(workdir=workdir, timeout=timeout)
        return fetch.get(url, format=format, headers=headers)
    finally:
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


def download_file(url: str, filename: Optional[str] = None, 
                 workdir: Optional[str] = None, headers: Optional[Dict] = None,
                 timeout: int = 30) -> Dict[str, Any]:
    """
    Download file from URL
    
    Args:
        url: Target URL
        filename: Save as filename (auto-detect if None)
        workdir: Working directory (creates temp dir if None)
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        {
            'success': bool,
            'file_path': str,
            'size': int,
            'content_type': str,
            'error': str  # On failure
        }
    """
    temp_dir = None
    if workdir is None:
        temp_dir = tempfile.mkdtemp(prefix="download_")
        workdir = temp_dir
    
    fetch = Fetch(workdir=workdir, timeout=timeout)
    return fetch.download(url, filename=filename, headers=headers)


# ============================================================================
# File Operation Functions
# ============================================================================

def read_file(file_path: str, workdir: str, start_line: Optional[int] = None,
             end_line: Optional[int] = None) -> Dict[str, Any]:
    """
    Read file content with optional line range
    
    Args:
        file_path: Relative path from workdir
        workdir: Working directory root
        start_line: Starting line number (1-based, inclusive)
        end_line: Ending line number (1-based, inclusive)
        
    Returns:
        {
            'success': bool,
            'content': str,
            'file_path': str,
            'total_lines': int,
            'error': str  # On failure
        }
    """
    file_ops = File(workdir=workdir)
    return file_ops.read_file(file_path, start_line=start_line, end_line=end_line)


def create_file(file_path: str, content: str, workdir: str) -> Dict[str, Any]:
    """
    Create new file with content
    
    Args:
        file_path: Relative path from workdir
        content: File content
        workdir: Working directory root
        
    Returns:
        {
            'success': bool,
            'file_path': str,
            'error': str  # On failure
        }
    """
    file_ops = File(workdir=workdir)
    return file_ops.create_file(file_path, content)


def replace_in_file(file_path: str, replacements: List[Dict[str, Any]], 
                   workdir: str) -> Dict[str, Any]:
    """
    Precisely replace text in file
    
    Args:
        file_path: Relative path from workdir
        replacements: List of replacement operations
            [
                {
                    'original_text': str,
                    'new_text': str,
                    'replace_all': bool  # Default: False
                }
            ]
        workdir: Working directory root
        
    Returns:
        {
            'success': bool,
            'replacements_made': int,
            'error': str  # On failure
        }
    """
    file_ops = File(workdir=workdir)
    return file_ops.search_replace(file_path, replacements)


def delete_file(file_path: str, workdir: str) -> Dict[str, Any]:
    """
    Delete file
    
    Args:
        file_path: Relative path from workdir
        workdir: Working directory root
        
    Returns:
        {
            'success': bool,
            'error': str  # On failure
        }
    """
    file_ops = File(workdir=workdir)
    return file_ops.delete_file(file_path)


def list_files(directory: str = '.', workdir: str = '.', 
              recursive: bool = False) -> Dict[str, Any]:
    """
    List files in directory
    
    Args:
        directory: Relative path from workdir
        workdir: Working directory root
        recursive: List recursively
        
    Returns:
        {
            'success': bool,
            'files': List[str],
            'directories': List[str],
            'error': str  # On failure
        }
    """
    file_ops = File(workdir=workdir)
    return file_ops.list_files(directory=directory, recursive=recursive)


# ============================================================================
# Process Management Functions
# ============================================================================

def list_processes(filter: Optional[str] = None, 
                  sort_by: str = 'cpu') -> Dict[str, Any]:
    """
    List running processes
    
    Args:
        filter: Filter by process name (substring match)
        sort_by: Sort by 'cpu', 'memory', 'pid', or 'name'
        
    Returns:
        {
            'success': bool,
            'processes': List[Dict],
            'count': int,
            'error': str  # On failure
        }
    """
    proc_mgr = Process()
    return proc_mgr.list(filter=filter, sort_by=sort_by)


def get_process_info(pid: int) -> Dict[str, Any]:
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
            'cmdline': List[str],
            'cwd': str,
            'create_time': float,
            'error': str  # On failure
        }
    """
    proc_mgr = Process()
    return proc_mgr.info(pid)


def kill_process(pid: int, force: bool = False, 
                allow_system: bool = False) -> Dict[str, Any]:
    """
    Terminate a process
    
    Args:
        pid: Process ID
        force: Force kill (SIGKILL) instead of graceful termination
        allow_system: Allow killing system processes
        
    Returns:
        {
            'success': bool,
            'pid': int,
            'name': str,
            'error': str  # On failure
        }
    """
    proc_mgr = Process(allow_system_processes=allow_system)
    return proc_mgr.kill(pid, force=force)


# ============================================================================
# System Information Functions
# ============================================================================

def get_system_info() -> Dict[str, Any]:
    """
    Get general system information
    
    Returns:
        {
            'success': bool,
            'platform': str,
            'platform_version': str,
            'architecture': str,
            'hostname': str,
            'cpu_count': int,
            'cpu_percent': float,
            'memory_total_gb': float,
            'memory_used_gb': float,
            'memory_percent': float,
            'boot_time': str,
            'uptime_hours': float,
            'error': str  # On failure
        }
    """
    sys_info = System()
    return sys_info.info()


def get_disk_usage(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get disk usage information
    
    Args:
        path: Path to check (default: current directory)
        
    Returns:
        {
            'success': bool,
            'path': str,
            'total_gb': float,
            'used_gb': float,
            'free_gb': float,
            'percent': float,
            'mount_point': str,
            'error': str  # On failure
        }
    """
    sys_info = System()
    return sys_info.disk(path=path)


def get_network_status() -> Dict[str, Any]:
    """
    Get network status and statistics
    
    Returns:
        {
            'success': bool,
            'connections': int,
            'bytes_sent_mb': float,
            'bytes_recv_mb': float,
            'packets_sent': int,
            'packets_recv': int,
            'interfaces': List[Dict],
            'error': str  # On failure
        }
    """
    sys_info = System()
    return sys_info.network()


def get_env_var(key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get environment variables
    
    Args:
        key: Specific variable key (returns all if None)
        
    Returns:
        {
            'success': bool,
            'variables': Dict[str, str],  # If key is None
            'key': str,                   # If key provided
            'value': str,                 # If key provided
            'count': int,                 # If key is None
            'error': str                  # On failure
        }
    """
    sys_info = System()
    return sys_info.env(key=key)
