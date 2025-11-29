import requests
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import mimetypes


class Fetch:
    """
    ⚠️ WARNING: For development/testing only, NOT for production use
    ⚠️ WARNING: No rate limiting or anti-spider protection
    ⚠️ WARNING: Downloads are restricted to workdir
    
    HTTP fetch toolkit - Clean API for LLM web operations
    
    Design principles:
    - Minimal public API (get, download)
    - Response format controlled by parameters
    - Structured return values
    - Cross-platform compatible
    """
    
    def __init__(self, workdir: str, timeout: int = 30):
        """
        Args:
            workdir: Working directory for downloaded files
            timeout: Request timeout in seconds
        """
        self.workdir = Path(workdir).absolute()
        self.timeout = timeout
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # Default headers to avoid basic blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get(self, url: str, format: str = 'content', headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Fetch content from URL
        
        Args:
            url: Target URL
            format: Response format
                - 'content': Extract clean text content (default)
                - 'raw': Return raw HTML/text
                - 'json': Parse as JSON
            headers: Optional additional headers
            
        Returns:
            {
                'success': bool,
                'content': str,          # Response content
                'url': str,              # Final URL (after redirects)
                'status_code': int,      # HTTP status code
                'content_type': str,     # Content-Type header
                'error': str             # Error message (on failure)
            }
        """
        if format not in ['content', 'raw', 'json']:
            return {
                'success': False,
                'error': f"Invalid format: {format}. Must be 'content', 'raw', or 'json'"
            }
        
        try:
            # Merge headers
            request_headers = {**self.headers, **(headers or {})}
            
            # Make request
            response = requests.get(url, headers=request_headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Process based on format
            if format == 'json':
                content = self._parse_json(response)
            elif format == 'content':
                content = self._extract_content(response)
            else:  # raw
                content = response.text
            
            return {
                'success': True,
                'content': content,
                'url': response.url,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', 'unknown')
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Request timeout after {self.timeout}s'
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'error': f'HTTP error: {e.response.status_code} {e.response.reason}'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def download(self, url: str, filename: Optional[str] = None, 
                 headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Download file from URL to workdir
        
        Args:
            url: Target URL
            filename: Save as filename (default: extract from URL)
            headers: Optional additional headers
            
        Returns:
            {
                'success': bool,
                'file_path': str,        # Saved file path
                'size': int,             # File size in bytes
                'content_type': str,     # Content-Type header
                'error': str             # Error message (on failure)
            }
        """
        try:
            # Merge headers
            request_headers = {**self.headers, **(headers or {})}
            
            # Make request with streaming
            response = requests.get(url, headers=request_headers, 
                                  timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Determine filename
            if not filename:
                filename = self._get_filename_from_response(response, url)
            
            # Validate path
            file_path = self.workdir / filename
            try:
                file_path.resolve().relative_to(self.workdir.resolve())
            except ValueError:
                return {
                    'success': False,
                    'error': f'Invalid filename: {filename} (outside workdir)'
                }
            
            # Download file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            size = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        size += len(chunk)
            
            return {
                'success': True,
                'file_path': str(file_path),
                'size': size,
                'content_type': response.headers.get('Content-Type', 'unknown')
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Download timeout after {self.timeout}s'
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'error': f'HTTP error: {e.response.status_code} {e.response.reason}'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Download error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _extract_content(self, response: requests.Response) -> str:
        """Extract clean text content from HTML response"""
        content_type = response.headers.get('Content-Type', '').lower()
        
        # If not HTML, return raw text
        if 'html' not in content_type:
            return response.text
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, and other non-content tags
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()
        
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        return text
    
    def _parse_json(self, response: requests.Response) -> Any:
        """Parse JSON response"""
        return response.json()
    
    def _get_filename_from_response(self, response: requests.Response, url: str) -> str:
        """Extract filename from response or URL"""
        # Try Content-Disposition header
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            return filename
        
        # Extract from URL
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        filename = Path(unquote(parsed.path)).name
        
        if not filename:
            # Generate filename from domain
            filename = f"{parsed.netloc.replace('.', '_')}_download"
            
            # Try to add extension from content-type
            content_type = response.headers.get('Content-Type', '')
            if content_type:
                ext = mimetypes.guess_extension(content_type.split(';')[0])
                if ext:
                    filename += ext
        
        return filename or 'download'
    
    def __repr__(self):
        return f"<Fetch workdir={self.workdir}>"


def demo():
    """Demo usage example"""
    print("=== Fetch Operations Demo ===\n")
    
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix="fetch_demo_")
    fetch = Fetch(workdir=temp_dir)
    
    print(f"Working directory: {fetch.workdir}\n")
    
    # 1. Get clean content from URL
    print("1. Get clean content (format='content'):")
    url = "https://httpbin.org/html"
    result = fetch.get(url, format='content')
    if result['success']:
        print(f"   Status: {result['status_code']}")
        print(f"   Content preview: {result['content'][:200]}...\n")
    else:
        print(f"   Error: {result['error']}\n")
    
    # 2. Get raw HTML
    print("2. Get raw HTML (format='raw'):")
    result = fetch.get(url, format='raw')
    if result['success']:
        print(f"   Raw preview: {result['content'][:150]}...\n")
    
    # 3. Get JSON
    print("3. Get JSON (format='json'):")
    json_url = "https://httpbin.org/json"
    result = fetch.get(json_url, format='json')
    if result['success']:
        print(f"   JSON type: {type(result['content'])}")
        print(f"   Content: {result['content']}\n")
    
    # 4. Download file
    print("4. Download file:")
    download_url = "https://httpbin.org/image/png"
    result = fetch.download(download_url, filename="test_image.png")
    if result['success']:
        print(f"   Saved to: {result['file_path']}")
        print(f"   Size: {result['size']} bytes")
        print(f"   Type: {result['content_type']}\n")
    
    # 5. Download with auto filename
    print("5. Download with auto filename:")
    result = fetch.download("https://httpbin.org/robots.txt")
    if result['success']:
        print(f"   Auto filename: {Path(result['file_path']).name}\n")
    
    # 6. Test error handling
    print("6. Test invalid URL:")
    result = fetch.get("https://invalid-domain-that-does-not-exist.com")
    print(f"   Result: {result}\n")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print("Demo completed. Temp directory cleaned.")


if __name__ == "__main__":
    demo()
