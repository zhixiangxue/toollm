<div align="center">
<a href="#"><img src="https://raw.githubusercontent.com/zhixiangxue/toollm/main/docs/assets/logo.png" alt="Demo Video" width="120"></a>

[![PyPI version](https://badge.fury.io/py/toollm.svg)](https://badge.fury.io/py/toollm)
[![Python Version](https://img.shields.io/pypi/pyversions/toollm)](https://pypi.org/project/toollm/)
[![License](https://img.shields.io/github/license/zhixiangxue/toollm)](https://github.com/zhixiangxue/toollm/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/toollm)](https://pypi.org/project/toollm/)

**Essential tools for LLMs to interact with the real world.**

toollm provides command execution, file operations, web scraping, process management, and system monitoring capabilities. Works seamlessly with LLMs.

</div>



---

## ⚠️ Important Warnings

**For Development/Testing Only - NOT for Production Use**

toollm provides system interaction capabilities, which come with inherent risks:

- **CommandRunner**: Executes shell commands with basic sandboxing. Assumes LLM-generated commands are trusted. Only defends against accidents, not malicious attacks. Do not use in untrusted environments.

- **Fetch**: No rate limiting or anti-spider protection. Use responsibly.

- **File**: Only supports text files. All operations restricted to workdir, but path traversal risks exist.

- **Process**: Can affect system stability. Use kill operations with extreme caution.

- **System**: May expose sensitive system information.

These tools are designed for development and testing scenarios where you control the LLM's behavior. Use in production at your own risk.

---

## Core Features

### 🌻 Dual API Design

Use whichever fits your workflow:

```python
# Class API - when you need state and reusability
runner = CommandRunner(workdir="./workspace")
result = runner.execute("ls -la")

# Function API - for stateless calls and AI framework integration
from toollm import execute_command
result = execute_command("ls -la", workdir="./workspace")
```

- **Class API**: Perfect for maintaining state and reusing instances
- **Function API**: Drop-in tools

### 🌱 Five Essential Tools

**CommandRunner** - Cross-platform sandboxed command execution
```python
with CommandRunner() as runner:
    result = runner.execute("echo 'Hello!'")
    print(result['stdout'])
```

**Fetch** - HTTP requests and web content extraction
```python
fetch = Fetch(workdir="./downloads")
result = fetch.get("https://example.com", format='content')  # Clean text
result = fetch.download("https://example.com/file.pdf")      # Download files
```

**File** - Structured file operations with safety boundaries
```python
file_ops = File(workdir="./workspace")
result = file_ops.create_file("test.py", "print('Hello')")
result = file_ops.search_replace("test.py", [{
    'original_text': "Hello",
    'new_text': "Hi there"
}])
```

**Process** - Process monitoring and management
```python
proc = Process()
result = proc.list(filter='python', sort_by='cpu')
result = proc.info(pid=1234)
```

**System** - System resource information
```python
sys = System()
result = sys.info()      # CPU, memory, uptime
result = sys.disk()      # Disk usage
result = sys.network()   # Network stats
```

### 🪴 Structured Returns

Every operation returns a consistent dictionary format:

```python
{
    'success': bool,
    'content': ...,      # Operation result
    'error': str         # Error message (on failure)
}
```

LLMs can easily parse and handle these responses.

---

## Quick Start

### Installation

```bash
pip install toollm
```

### Execute Commands

```python
from toollm import CommandRunner

# Auto-managed temp directory
with CommandRunner() as runner:
    result = runner.execute("echo 'Hello LLM!'")
    if result['success']:
        print(result['stdout'])
```

**Function style:**

```python
from toollm import execute_command

result = execute_command("ls -la", workdir="./workspace")
```

### Fetch Web Content

```python
from toollm import Fetch

fetch = Fetch(workdir="./downloads")

# Get clean text content
result = fetch.get("https://example.com", format='content')

# Get raw HTML
result = fetch.get("https://example.com", format='raw')

# Parse JSON API
result = fetch.get("https://api.example.com/data", format='json')

# Download files
result = fetch.download("https://example.com/file.pdf")
```

**Function style:**

```python
from toollm import fetch_url, download_file

result = fetch_url("https://example.com", format='content')
result = download_file("https://example.com/file.pdf", workdir="./downloads")
```

### File Operations

```python
from toollm import File

file_ops = File(workdir="./workspace")

# Create file
file_ops.create_file("test.py", "print('Hello')")

# Read file (with optional line range)
result = file_ops.read_file("test.py")
result = file_ops.read_file("test.py", start_line=1, end_line=5)

# Precise search and replace
file_ops.search_replace("test.py", [
    {
        'original_text': "print('Hello')",
        'new_text': "print('Hello LLM!')",
        'replace_all': False
    }
])

# List files
result = file_ops.list_files(recursive=True)

# Delete file
file_ops.delete_file("test.py")
```

**Function style:**

```python
from toollm import read_file, create_file, replace_in_file

read_file("test.py", workdir="./workspace")
create_file("test.py", "print('Hello')", workdir="./workspace")
replace_in_file("test.py", [{'original_text': "Hello", 'new_text': "Hi"}], workdir="./workspace")
```

### Process Management

```python
from toollm import Process

proc = Process()

# List processes (sorted by CPU usage)
result = proc.list(sort_by='cpu')
for p in result['processes'][:10]:
    print(f"{p['name']}: {p['cpu_percent']}%")

# Filter by name
result = proc.list(filter='python', sort_by='memory')

# Get detailed info
result = proc.info(pid=1234)

# Terminate process (use with caution)
result = proc.kill(pid=1234)
```

**Function style:**

```python
from toollm import list_processes, get_process_info, kill_process

list_processes(filter='python', sort_by='cpu')
get_process_info(pid=1234)
kill_process(pid=1234)
```

### System Monitoring

```python
from toollm import System

sys = System()

# System information
result = sys.info()
print(f"CPU: {result['cpu_percent']}%")
print(f"Memory: {result['memory_used_gb']}GB / {result['memory_total_gb']}GB")

# Disk usage
result = sys.disk(path="/")
print(f"Disk: {result['used_gb']}GB / {result['total_gb']}GB")

# Network status
result = sys.network()
print(f"Connections: {result['connections']}")
print(f"Sent: {result['bytes_sent_mb']}MB")

# Environment variables
result = sys.env(key='PATH')
```

**Function style:**

```python
from toollm import get_system_info, get_disk_usage, get_network_status, get_env_var

get_system_info()
get_disk_usage(path="/")
get_network_status()
get_env_var(key='PATH')
```

---

## Design Principles

- **Structured Returns**: All operations return consistent dict format with `success` and `error` fields
- **Safety Boundaries**: File operations restricted to workdir, command execution has basic protections
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Development Focus**: Designed for development/testing, not production use

---

## Examples

Each module includes a standalone demo:

```bash
python -m toollm.cmd       # Command execution examples
python -m toollm.fetch     # Web fetching examples
python -m toollm.file      # File operation examples
python -m toollm.process   # Process management examples
python -m toollm.system    # System monitoring examples
```

---

## Is toollm for You?

If you:
- Need to give LLMs real-world interaction capabilities
- Want simple, structured tool responses
- Are building with LangChain, OpenAI, or other AI frameworks
- Need both class-based and function-based APIs

Then toollm is made for you.

---

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

Issues and Pull Requests are welcome!

<div align="right">
<a href="#"><img src="https://raw.githubusercontent.com/zhixiangxue/toollm/main/docs/assets/logo.png" alt="Demo Video" width="120"></a>
</div>
