import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil


class CommandRunner:
    """
    ⚠️ WARNING: For development/testing only, NOT for production use
    ⚠️ WARNING: Assumes LLM-generated commands are trusted, only defends against accidents
    ⚠️ WARNING: Cannot defend against malicious commands, do not use in untrusted environments
    
    Command executor - Cross-platform command sandbox designed for LLM
    
    Design principles:
    - LLM handles platform adaptation, this just executes
    - Trust LLM won't intentionally generate malicious commands
    - Prevent "accidents" not "malicious attacks"
    - All operations restricted to workdir
    """
    
    def __init__(self, workdir: Optional[str] = None, timeout: int = 60):
        """
        Args:
            workdir: Working directory, creates temp dir if None
            timeout: Command execution timeout in seconds
        """
        self.timeout = timeout
        
        # Setup working directory
        if workdir:
            self.workdir = Path(workdir).absolute()
            self.workdir.mkdir(parents=True, exist_ok=True)
            self._is_temp = False
        else:
            self.workdir = Path(tempfile.mkdtemp(prefix="llm_cmd_"))
            self._is_temp = True
        
        # System-level dangerous operation blacklist (only blocks obvious destructive commands)
        self.blocked_patterns = [
            'rm -rf /',
            'rm -rf /*',
            'format c:',
            'shutdown',
            'reboot',
            'halt',
            'poweroff',
            'mkfs',
            'fdisk',
        ]
    
    def _is_blocked(self, command: str) -> bool:
        """Check if command is obviously dangerous"""
        cmd_lower = command.lower().strip()
        return any(pattern in cmd_lower for pattern in self.blocked_patterns)
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute command
        
        Args:
            command: Command to execute (LLM already adapted for platform)
            **kwargs: Additional subprocess parameters
            
        Returns:
            {
                'success': bool,        # Execution success
                'returncode': int,      # Return code
                'stdout': str,          # Standard output
                'stderr': str,          # Standard error
                'workdir': str,         # Working directory
                'error': str            # Error message (on failure only)
            }
        """
        # Check obviously dangerous commands
        if self._is_blocked(command):
            return {
                'success': False,
                'error': f'Blocked dangerous command: {command}',
                'returncode': -1,
                'stdout': '',
                'stderr': '',
                'workdir': str(self.workdir)
            }
        
        try:
            # Execute in working directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=kwargs.get('timeout', self.timeout),
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'workdir': str(self.workdir)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timeout after {self.timeout}s',
                'returncode': -1,
                'stdout': '',
                'stderr': '',
                'workdir': str(self.workdir)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)}',
                'returncode': -1,
                'stdout': '',
                'stderr': '',
                'workdir': str(self.workdir)
            }
    
    def list_files(self) -> list:
        """List files in working directory"""
        try:
            return [f.name for f in self.workdir.iterdir()]
        except Exception:
            return []
    
    def read_file(self, filename: str) -> Optional[str]:
        """Read file content from working directory"""
        try:
            file_path = self.workdir / filename
            # Ensure file is within workdir
            file_path.resolve().relative_to(self.workdir.resolve())
            return file_path.read_text()
        except Exception as e:
            return None
    
    def write_file(self, filename: str, content: str) -> bool:
        """Write file to working directory"""
        try:
            file_path = self.workdir / filename
            # Ensure file is within workdir
            file_path.resolve().relative_to(self.workdir.resolve())
            file_path.write_text(content)
            return True
        except Exception:
            return False
    
    def cleanup(self):
        """Cleanup temporary working directory"""
        if self._is_temp and self.workdir.exists():
            shutil.rmtree(self.workdir)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def __repr__(self):
        return f"<CommandRunner workdir={self.workdir}>"


def demo():
    """Demo usage example"""
    print("=== LLM Command Runner Demo ===")
    
    # Use temporary directory
    with CommandRunner() as runner:
        print(f"\nWorkdir: {runner.workdir}\n")
        
        # Example: Simulate LLM-returned command sequence
        commands = [
            "echo 'Hello from LLM!' > test.txt",
            "ls -la" if os.name != 'nt' else "dir",
            "cat test.txt" if os.name != 'nt' else "type test.txt",
            "python --version",
        ]
        
        for cmd in commands:
            print(f"Execute: {cmd}")
            result = runner.execute(cmd)
            
            if result['success']:
                print(f"Success (returncode={result['returncode']})")
                if result['stdout']:
                    print(f"Output:\n{result['stdout']}")
            else:
                print(f"Failed")
                if 'error' in result:
                    print(f"Error: {result['error']}")
                if result['stderr']:
                    print(f"stderr: {result['stderr']}")
            print()
        
        # Test dangerous command blocking
        print("\nTest dangerous command blocking:")
        dangerous = "rm -rf /"
        print(f"Execute: {dangerous}")
        result = runner.execute(dangerous)
        print(f"Result: {result}\n")
        
        print(f"Workdir files: {runner.list_files()}")
    
    print("\nTemp directory auto-cleaned")


if __name__ == "__main__":
    demo()