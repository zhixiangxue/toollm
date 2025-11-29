import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import shutil


class File:
    """
    ⚠️ WARNING: For development/testing only, NOT for production use
    ⚠️ WARNING: Only supports text files, binary files will be rejected
    ⚠️ WARNING: All operations restricted to workdir
    
    File operations toolkit - Qoder-like structured file operations for LLM
    
    Design principles:
    - Structured return values (always dict with success/error)
    - Only handle text files (let CommandRunner handle complex conversions)
    - Path validation to prevent directory traversal
    - Cross-platform compatible
    """
    
    SUPPORTED_TEXT_EXTENSIONS = {
        '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json', 
        '.yaml', '.yml', '.html', '.css', '.scss', '.sh', '.bat', 
        '.csv', '.log', '.xml', '.sql', '.env', '.ini', '.cfg',
        '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb'
    }
    
    def __init__(self, workdir: str):
        """
        Args:
            workdir: Working directory root for all file operations
        """
        self.workdir = Path(workdir).absolute()
        if not self.workdir.exists():
            self.workdir.mkdir(parents=True, exist_ok=True)
    
    def _validate_path(self, file_path: str) -> tuple[bool, Optional[Path]]:
        """
        Validate file path is within workdir
        Returns: (is_valid, resolved_path)
        """
        try:
            full_path = (self.workdir / file_path).resolve()
            # Security check: ensure path is within workdir
            full_path.relative_to(self.workdir)
            return True, full_path
        except (ValueError, RuntimeError):
            return False, None
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file extension is supported text type"""
        return file_path.suffix.lower() in self.SUPPORTED_TEXT_EXTENSIONS
    
    def read_file(self, file_path: str, start_line: Optional[int] = None, 
                  end_line: Optional[int] = None) -> Dict[str, Any]:
        """
        Read file content with optional line range
        
        Args:
            file_path: Relative path from workdir
            start_line: Starting line number (1-based, inclusive)
            end_line: Ending line number (1-based, inclusive)
            
        Returns:
            {
                'success': bool,
                'content': str,          # File content
                'file_path': str,        # Full path
                'total_lines': int,      # Total line count
                'error': str             # Error message (on failure)
            }
        """
        is_valid, full_path = self._validate_path(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid path: {file_path} (outside workdir)'
            }
        
        if not full_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        if not self._is_text_file(full_path):
            return {
                'success': False,
                'error': f'Unsupported file type: {full_path.suffix}. Only text files supported.'
            }
        
        try:
            content = full_path.read_text(encoding='utf-8')
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)
            
            # Apply line range if specified
            if start_line is not None and end_line is not None:
                if start_line < 1 or end_line > total_lines:
                    return {
                        'success': False,
                        'error': f'Line range out of bounds: {start_line}-{end_line} (total: {total_lines})'
                    }
                lines = lines[start_line-1:end_line]
                content = ''.join(lines)
            
            return {
                'success': True,
                'content': content,
                'file_path': str(full_path),
                'total_lines': total_lines
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Read error: {str(e)}'
            }
    
    def create_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Create new file with content
        
        Args:
            file_path: Relative path from workdir
            content: File content to write
            
        Returns:
            {
                'success': bool,
                'file_path': str,
                'error': str
            }
        """
        is_valid, full_path = self._validate_path(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid path: {file_path}'
            }
        
        if full_path.exists():
            return {
                'success': False,
                'error': f'File already exists: {file_path}'
            }
        
        if not self._is_text_file(full_path):
            return {
                'success': False,
                'error': f'Unsupported file type: {full_path.suffix}'
            }
        
        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            
            return {
                'success': True,
                'file_path': str(full_path)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Create error: {str(e)}'
            }
    
    def search_replace(self, file_path: str, 
                      replacements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Precisely replace text in file (Qoder-style)
        
        Args:
            file_path: Relative path from workdir
            replacements: List of replacement operations
                [
                    {
                        'original_text': str,   # Text to find (must be unique if not replace_all)
                        'new_text': str,        # Replacement text
                        'replace_all': bool     # Replace all occurrences (default: False)
                    }
                ]
        
        Returns:
            {
                'success': bool,
                'replacements_made': int,
                'error': str
            }
        """
        is_valid, full_path = self._validate_path(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid path: {file_path}'
            }
        
        if not full_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        try:
            content = full_path.read_text(encoding='utf-8')
            replacements_made = 0
            
            for idx, replacement in enumerate(replacements):
                original = replacement.get('original_text')
                new_text = replacement.get('new_text')
                replace_all = replacement.get('replace_all', False)
                
                if original is None or new_text is None:
                    return {
                        'success': False,
                        'error': f'Replacement {idx}: missing original_text or new_text'
                    }
                
                if original == new_text:
                    return {
                        'success': False,
                        'error': f'Replacement {idx}: original_text and new_text are identical'
                    }
                
                count = content.count(original)
                
                if count == 0:
                    return {
                        'success': False,
                        'error': f'Replacement {idx}: original_text not found in file'
                    }
                
                if not replace_all and count > 1:
                    return {
                        'success': False,
                        'error': f'Replacement {idx}: original_text appears {count} times (not unique). Set replace_all=true or make original_text more specific.'
                    }
                
                if replace_all:
                    content = content.replace(original, new_text)
                    replacements_made += count
                else:
                    content = content.replace(original, new_text, 1)
                    replacements_made += 1
            
            full_path.write_text(content, encoding='utf-8')
            
            return {
                'success': True,
                'replacements_made': replacements_made
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Replace error: {str(e)}'
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file
        
        Args:
            file_path: Relative path from workdir
            
        Returns:
            {
                'success': bool,
                'error': str
            }
        """
        is_valid, full_path = self._validate_path(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid path: {file_path}'
            }
        
        if not full_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        if full_path.is_dir():
            return {
                'success': False,
                'error': f'Path is a directory, not a file: {file_path}'
            }
        
        try:
            full_path.unlink()
            return {'success': True}
        except Exception as e:
            return {
                'success': False,
                'error': f'Delete error: {str(e)}'
            }
    
    def list_files(self, directory: str = '.', recursive: bool = False) -> Dict[str, Any]:
        """
        List files in directory
        
        Args:
            directory: Relative path from workdir (default: '.')
            recursive: List recursively
            
        Returns:
            {
                'success': bool,
                'files': List[str],      # List of file paths
                'directories': List[str], # List of directory paths
                'error': str
            }
        """
        is_valid, full_path = self._validate_path(directory)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid path: {directory}'
            }
        
        if not full_path.exists():
            return {
                'success': False,
                'error': f'Directory not found: {directory}'
            }
        
        if not full_path.is_dir():
            return {
                'success': False,
                'error': f'Path is not a directory: {directory}'
            }
        
        try:
            files = []
            directories = []
            
            if recursive:
                for item in full_path.rglob('*'):
                    rel_path = item.relative_to(self.workdir)
                    if item.is_file():
                        files.append(str(rel_path))
                    elif item.is_dir():
                        directories.append(str(rel_path))
            else:
                for item in full_path.iterdir():
                    rel_path = item.relative_to(self.workdir)
                    if item.is_file():
                        files.append(str(rel_path))
                    elif item.is_dir():
                        directories.append(str(rel_path))
            
            return {
                'success': True,
                'files': sorted(files),
                'directories': sorted(directories)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'List error: {str(e)}'
            }
    
    def __repr__(self):
        return f"<File workdir={self.workdir}>"


def demo():
    """Demo usage example"""
    print("=== File Operations Demo ===\n")
    
    # Create File instance with temp directory
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="file_demo_")
    file_ops = File(workdir=temp_dir)
    
    print(f"Working directory: {file_ops.workdir}\n")
    
    # 1. Create a new file
    print("1. Create file:")
    result = file_ops.create_file("test.py", "def hello():\n    print('Hello World')\n")
    print(f"   Result: {result}\n")
    
    # 2. Read file
    print("2. Read file:")
    result = file_ops.read_file("test.py")
    if result['success']:
        print(f"   Content:\n{result['content']}")
        print(f"   Total lines: {result['total_lines']}\n")
    
    # 3. Read file with line range
    print("3. Read file (lines 1-1):")
    result = file_ops.read_file("test.py", start_line=1, end_line=1)
    if result['success']:
        print(f"   Content: {result['content']}\n")
    
    # 4. Search and replace
    print("4. Search and replace:")
    result = file_ops.search_replace("test.py", [
        {
            'original_text': "print('Hello World')",
            'new_text': "print('Hello LLM!')",
            'replace_all': False
        }
    ])
    print(f"   Result: {result}\n")
    
    # 5. Read modified file
    print("5. Read modified file:")
    result = file_ops.read_file("test.py")
    if result['success']:
        print(f"   Content:\n{result['content']}\n")
    
    # 6. Create nested file
    print("6. Create nested file:")
    result = file_ops.create_file("subdir/config.json", '{\n  "name": "test"\n}\n')
    print(f"   Result: {result}\n")
    
    # 7. List files
    print("7. List files (non-recursive):")
    result = file_ops.list_files()
    print(f"   Files: {result.get('files')}")
    print(f"   Directories: {result.get('directories')}\n")
    
    print("8. List files (recursive):")
    result = file_ops.list_files(recursive=True)
    print(f"   Files: {result.get('files')}\n")
    
    # 9. Try to read unsupported file type
    print("9. Try unsupported file type:")
    result = file_ops.create_file("test.pdf", "fake pdf")
    print(f"   Result: {result}\n")
    
    # 10. Delete file
    print("10. Delete file:")
    result = file_ops.delete_file("test.py")
    print(f"   Result: {result}\n")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print("Demo completed. Temp directory cleaned.")


if __name__ == "__main__":
    demo()
