"""toollm - Tools for LLM

A toolkit that enhances LLM capabilities in:
- Command execution (CommandRunner)
- Web content fetching (Fetch)
- File operations (File)
- Process management (Process)
- System monitoring (System)

Provides both class-based and function-based APIs for flexibility.
"""

# Class-based API
from .cmd import CommandRunner
from .fetch import Fetch
from .file import File
from .process import Process
from .system import System

# Function-based API
from .functions import (
    # Command functions
    execute_command,
    list_workdir_files,
    read_workdir_file,
    write_workdir_file,
    # Fetch functions
    fetch_url,
    download_file,
    # File functions
    read_file,
    create_file,
    replace_in_file,
    delete_file,
    list_files,
    # Process functions
    list_processes,
    get_process_info,
    kill_process,
    # System functions
    get_system_info,
    get_disk_usage,
    get_network_status,
    get_env_var,
)

__version__ = "0.1.0"

__all__ = [
    # Classes
    "CommandRunner",
    "Fetch",
    "File",
    "Process",
    "System",
    # Functions - Command
    "execute_command",
    "list_workdir_files",
    "read_workdir_file",
    "write_workdir_file",
    # Functions - Fetch
    "fetch_url",
    "download_file",
    # Functions - File
    "read_file",
    "create_file",
    "replace_in_file",
    "delete_file",
    "list_files",
    # Functions - Process
    "list_processes",
    "get_process_info",
    "kill_process",
    # Functions - System
    "get_system_info",
    "get_disk_usage",
    "get_network_status",
    "get_env_var",
]