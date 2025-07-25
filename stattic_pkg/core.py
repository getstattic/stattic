import os
import shutil
import markdown
import hashlib
import yaml
import argparse
import logging
import time
import tempfile
import html
import threading
import gc
import atexit
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
import re
import requests
from PIL import Image
import csscompressor
import rjsmin
import mistune
from xml.sax.saxutils import escape
from urllib.parse import urlparse
from email.utils import formatdate
from hashlib import md5
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
import pkg_resources
from .url_validator import URLValidator, SafeRequestor

GOOGLE_FONTS_API = 'https://fonts.googleapis.com/css2?family={font_name}:wght@{weights}&display=swap'

# Thread-local storage for FileProcessor instances
thread_local = threading.local()

def initializer(
    templates_dir: str, 
    output_dir: str, 
    images_dir: str, 
    categories: Dict[int, Any], 
    tags: Dict[int, Any], 
    authors: Dict[int, Any], 
    pages: List[Dict[str, Any]], 
    site_url: str, 
    content_dir: str, 
    blog_slug: str
) -> None:
    """Initialize FileProcessor instance in thread-local storage for each worker process."""
    session = requests.Session()
    # Initialize URL validator and safe requestor for each worker
    url_validator = URLValidator()
    safe_requestor = SafeRequestor(url_validator, session)
    thread_local.file_processor = FileProcessor(templates_dir, output_dir, images_dir, categories, tags, authors, pages, site_url, content_dir, blog_slug, session=session, safe_requestor=safe_requestor)

    # Register cleanup to close session when process ends
    import atexit
    atexit.register(cleanup_session)

def cleanup_session() -> None:
    """Cleanup function to close session when worker process ends."""
    if hasattr(thread_local, 'file_processor') and hasattr(thread_local.file_processor, 'session'):
        try:
            thread_local.file_processor.session.close()
        except:
            pass  # Ignore errors during cleanup

def process_file(file_path: str, is_page: bool) -> Dict[str, Any]:
    """Process a file using the thread-local FileProcessor."""
    return thread_local.file_processor.process(file_path, is_page)

class FileProcessor:
    def __init__(
        self, 
        templates_dir: str, 
        output_dir: str, 
        images_dir: str, 
        categories: Dict[int, Any], 
        tags: Dict[int, Any], 
        authors: Dict[int, Any], 
        pages: List[Dict[str, Any]], 
        site_url: str, 
        content_dir: str, 
        blog_slug: str, 
        session: Optional[requests.Session] = None, 
        safe_requestor: Optional[Any] = None
    ) -> None:
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.images_dir = images_dir
        self.categories = categories
        self.tags = tags
        self.authors = authors
        self.pages = pages
        self.site_url = site_url
        self.content_dir = content_dir
        self.blog_slug = blog_slug
        self.session = session or requests.Session()
        self.logger = logging.getLogger('FileProcessor')

        # Initialize URL validation and safe requesting
        self.url_validator = URLValidator()
        self.safe_requestor = safe_requestor or SafeRequestor(self.url_validator, self.session)

        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.markdown_parser = self.create_markdown_parser()

    def markdown_filter(self, text: str) -> str:
        """Convert markdown text to HTML."""
        return self.markdown_parser(text)

    def create_markdown_parser(self) -> Any:
        """Create a Mistune markdown parser with a custom renderer."""
        class CustomRenderer(mistune.HTMLRenderer):
            def __init__(self) -> None:
                super().__init__(escape=False)
            def block_code(self, code: str, info: Optional[str] = None) -> str:
                escaped_code = mistune.escape(code)
                return '<pre style="white-space: pre-wrap;"><code>{}</code></pre>'.format(escaped_code)
        return mistune.create_markdown(
            renderer=CustomRenderer(),
            plugins=['table', 'task_lists', 'strikethrough']
        )

    def parse_date(self, date_str: Union[str, datetime, date]) -> datetime:
        """
        Parse a date string with enhanced format support and error handling.
        
        Supports 16 different date formats with performance optimization.
        Most common formats are checked first for better performance.
        
        Args:
            date_str: String, datetime, or date object to parse
            
        Returns:
            datetime: Parsed datetime object, or datetime.min if parsing fails
        """
        if isinstance(date_str, datetime):
            return date_str
        elif isinstance(date_str, date):
            return datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, str):
            # Strip whitespace and normalize
            date_str = date_str.strip()
            if not date_str:
                self.logger.warning("Empty date string provided, using minimum date")
                return datetime.min

            # Performance-optimized format list (most common first)
            date_formats = [
                '%Y-%m-%d',           # 2025-06-12 (most common)
                '%Y-%m-%dT%H:%M:%S',  # 2025-06-12T14:30:00 (ISO format)
                '%b %d, %Y',          # Jun 12, 2025 (short month)
                '%B %d, %Y',          # June 12, 2025 (full month)
                '%Y-%m-%d %H:%M:%S',  # 2025-06-12 14:30:00
                '%m/%d/%Y',           # 06/12/2025 (US format)
                '%d/%m/%Y',           # 12/06/2025 (EU format)
                '%Y/%m/%d',           # 2025/06/12 (Asian format)
                '%m-%d-%Y',           # 06-12-2025
                '%d-%m-%Y',           # 12-06-2025
                '%Y.%m.%d',           # 2025.06.12
                '%d.%m.%Y',           # 12.06.2025
                '%b %d %Y',           # Jun 12 2025 (no comma)
                '%B %d %Y',           # June 12 2025 (no comma)
                '%Y-%m-%dT%H:%M:%SZ', # 2025-06-12T14:30:00Z (UTC)
                '%Y-%m-%dT%H:%M:%S.%f' # 2025-06-12T14:30:00.123456 (microseconds)
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, log warning and return minimum date
            self.logger.warning(f"Unable to parse date '{date_str}' with any supported format. Using minimum date as fallback.")
            return datetime.min
        else:
            self.logger.warning(f"Invalid date type: {type(date_str)}. Expected string, date, or datetime.")
            return datetime.min

    def download_image(self, url: str, output_dir: str) -> Optional[str]:
        """Download an image and save it locally with comprehensive security protection."""
        # File extension validation
        if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')):
            return None
        # Ensure output directory exists
        try:
            if url.startswith('http'):
                # Validate URL for SSRF protection
                is_valid, error_msg = self.url_validator.validate_url(url)
                if not is_valid:
                    self.logger.warning(f"SSRF protection blocked URL {url}: {error_msg}")
                    return None

                # Enhanced filename sanitization - but check cache FIRST
                base_image_name = self._sanitize_filename_without_uniqueness(url)
                base_image_path = os.path.join(output_dir, base_image_name)
                base_webp_path = base_image_path.rsplit('.', 1)[0] + '.webp'

                # Caching: Check for WebP BEFORE making filename unique
                if os.path.exists(base_webp_path):
                    self.logger.info(f"Using cached WebP image: {base_webp_path}")
                    return base_webp_path  # Return cached WebP path instead of None

                # If not cached, now make filename unique for downloading
                image_name = self._make_filename_unique(base_image_name, output_dir)
                image_path = os.path.join(output_dir, image_name)
                webp_path = image_path.rsplit('.', 1)[0] + '.webp'

                # Make safe request with streaming enabled and size limit
                success, result = self.safe_requestor.safe_get(
                    url, 
                    timeout=30, 
                    allow_redirects=True,
                    stream=True  # Enable streaming for large files
                )
                if not success:
                    self.logger.warning(f"Failed to download image {url}: {result}")
                    return None

                # Enhanced memory management: Use context manager for response handling
                with result as response:
                    # Content-Type validation
                    content_type = response.headers.get('content-type', '').lower()
                    valid_content_types = {
                        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
                        'image/webp', 'image/bmp', 'image/tiff', 'image/tif'
                    }
                    if content_type and not any(ct in content_type for ct in valid_content_types):
                        self.logger.warning(f"Invalid content type for image {url}: {content_type}")
                        return None
                    
                    # File size validation (10MB limit)
                    content_length = response.headers.get('content-length')
                    max_size = 10 * 1024 * 1024  # 10MB
                    if content_length and int(content_length) > max_size:
                        self.logger.warning(f"Image too large {url}: {content_length} bytes (max {max_size})")
                        return None
                    
                    # Verify the final path is within output_dir (path traversal protection)
                    if not os.path.abspath(image_path).startswith(os.path.abspath(output_dir)):
                        self.logger.error(f"Path traversal attempt detected: {image_name}")
                        return None

                    # Enhanced memory management: Stream-based download with proper resource cleanup
                    try:
                        downloaded_size = 0
                        # Use context manager for file operations
                        with open(image_path, 'wb') as image_file:
                            # Process in chunks to minimize memory usage
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:  # filter out keep-alive chunks
                                    downloaded_size += len(chunk)
                                    # Runtime size check to prevent memory exhaustion
                                    if downloaded_size > max_size:
                                        self.logger.warning(f"Image download exceeded size limit during streaming {url}: {downloaded_size} bytes")
                                        # Remove partial file with proper error handling
                                        self._safe_remove_file(image_path)
                                        return None
                                    image_file.write(chunk)
                                    # Explicit chunk cleanup for large files
                                    del chunk

                        # Final size verification
                        if os.path.getsize(image_path) > max_size:
                            self.logger.warning(f"Downloaded image too large {url}: {os.path.getsize(image_path)} bytes")
                            self._safe_remove_file(image_path)
                            return None

                        self.logger.debug(f"Successfully downloaded image: {url} -> {image_name} ({downloaded_size} bytes)")
                        return image_path

                    except (IOError, OSError, PermissionError) as e:
                        self.logger.error(f"Failed to write downloaded image {image_path}: {e}")
                        # Clean up partial file with enhanced error handling
                        self._safe_remove_file(image_path)
                        return None

            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading image {url}: {e}")
            return None

    def _sanitize_filename_without_uniqueness(self, url: str) -> str:
        """Enhanced filename sanitization with security checks, but without uniqueness."""
        try:
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)

            # If no filename in path, generate from URL hash
            if not filename or '.' not in filename:
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                # Try to detect extension from URL or use .jpg as default
                if url.lower().endswith(('.png', '.gif', '.webp', '.bmp', '.tiff')):
                    ext = '.' + url.lower().split('.')[-1]
                else:
                    ext = '.jpg'
                filename = f"image_{url_hash}{ext}"

            # Remove query parameters and fragments
            filename = filename.split('?')[0].split('#')[0]

            # Comprehensive sanitization
            filename = os.path.basename(os.path.normpath(filename))

            # Remove dangerous characters and patterns
            dangerous_chars = '<>:"|?*\\/\x00-\x1f'
            for char in dangerous_chars:
                filename = filename.replace(char, '_')

            # Remove directory traversal sequences
            filename = filename.replace('..', '_')

            # Ensure filename isn't empty and has proper extension
            if not filename or len(filename) < 3:
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                filename = f"image_{url_hash}.jpg"

            # Ensure it has a valid image extension
            valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
            if not any(filename.lower().endswith(ext) for ext in valid_extensions):
                filename += '.jpg'

            # Length limit (255 characters for most filesystems)
            if len(filename) > 255:
                name_part, ext_part = os.path.splitext(filename)
                max_name_length = 255 - len(ext_part)
                filename = name_part[:max_name_length] + ext_part

            return filename

        except Exception as e:
            # Fallback to hash-based filename if sanitization fails
            self.logger.warning(f"Filename sanitization failed for {url}: {e}")
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            return f"image_{url_hash}.jpg"

    def _make_filename_unique(self, base_filename: str, output_dir: str) -> str:
        """Make filename unique if it already exists."""
        filename = base_filename
        original_filename = base_filename
        counter = 1
        
        while os.path.exists(os.path.join(output_dir, filename)):
            name_part, ext_part = os.path.splitext(original_filename)
            filename = f"{name_part}_{counter}{ext_part}"
            counter += 1
            # Prevent infinite loop
            if counter > 1000:
                url_hash = hashlib.md5(original_filename.encode()).hexdigest()[:12]
                filename = f"image_{url_hash}_{counter}.jpg"
                break
        
        return filename

    def _sanitize_filename(self, url: str, output_dir: str) -> str:
        """Enhanced filename sanitization with security checks."""
        try:
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)

            # If no filename in path, generate from URL hash
            if not filename or '.' not in filename:
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                # Try to detect extension from URL or use .jpg as default
                if url.lower().endswith(('.png', '.gif', '.webp', '.bmp', '.tiff')):
                    ext = '.' + url.lower().split('.')[-1]
                else:
                    ext = '.jpg'
                filename = f"image_{url_hash}{ext}"

            # Remove query parameters and fragments
            filename = filename.split('?')[0].split('#')[0]

            # Comprehensive sanitization
            filename = os.path.basename(os.path.normpath(filename))

            # Remove dangerous characters and patterns
            dangerous_chars = '<>:"|?*\\/\x00-\x1f'
            for char in dangerous_chars:
                filename = filename.replace(char, '_')

            # Remove directory traversal sequences
            filename = filename.replace('..', '_')

            # Ensure filename isn't empty and has proper extension
            if not filename or len(filename) < 3:
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                filename = f"image_{url_hash}.jpg"

            # Ensure it has a valid image extension
            valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
            if not any(filename.lower().endswith(ext) for ext in valid_extensions):
                filename += '.jpg'

            # Length limit (255 characters for most filesystems)
            if len(filename) > 255:
                name_part, ext_part = os.path.splitext(filename)
                max_name_length = 255 - len(ext_part)
                filename = name_part[:max_name_length] + ext_part

            # Check if file already exists and make unique if necessary
            original_filename = filename
            counter = 1
            while os.path.exists(os.path.join(output_dir, filename)):
                name_part, ext_part = os.path.splitext(original_filename)
                filename = f"{name_part}_{counter}{ext_part}"
                counter += 1
                # Prevent infinite loop
                if counter > 1000:
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                    filename = f"image_{url_hash}_{counter}.jpg"
                    break

            return filename

        except Exception as e:
            # Fallback to hash-based filename if sanitization fails
            self.logger.warning(f"Filename sanitization failed for {url}: {e}")
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            return f"image_{url_hash}.jpg"

    def _safe_remove_file(self, file_path: str) -> None:
        """Safely remove a file with proper error handling."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up file: {file_path}")
        except (OSError, PermissionError) as e:
            self.logger.warning(f"Failed to remove file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error removing file {file_path}: {e}")

    def convert_image_to_webp(self, image_path: str) -> Optional[str]:
        """Convert image to WebP format with enhanced memory management."""
        try:
            # Skip if path is a directory
            if os.path.isdir(image_path):
                return None

            # If input is already a WebP file, return it as-is (already cached)
            if image_path.lower().endswith('.webp'):
                if os.path.exists(image_path):
                    self.logger.debug(f"Image already in WebP format: {image_path}")
                    return image_path
                else:
                    return None

            ext = os.path.splitext(image_path)[1].lower()
            webp_path = image_path.rsplit('.', 1)[0] + '.webp'

            # Enhanced memory management for image processing
            try:
                if ext == ".gif":
                    # Process GIF with animation preservation and memory optimization
                    with Image.open(image_path) as img:
                        # Check if image is too large for memory-safe processing
                        width, height = img.size
                        pixel_count = width * height
                        # Conservative limit: ~50MP for animated GIFs
                        if pixel_count > 50_000_000:
                            self.logger.warning(f"GIF image too large for safe processing: {width}x{height} ({pixel_count} pixels)")
                            return None

                        # Preserve animation with lossless quality (matches old gif2webp -lossless)
                        img.save(webp_path, "WEBP", save_all=True, lossless=True, method=6)
                        # No explicit img.close() needed
                else:
                    # Process static images with memory optimization
                    with Image.open(image_path) as img:
                        # Memory optimization: Check image size
                        width, height = img.size
                        pixel_count = width * height
                        # Conservative limit: ~200MP for static images
                        if pixel_count > 200_000_000:
                            self.logger.warning(f"Static image too large for safe processing: {width}x{height} ({pixel_count} pixels)")
                            return None

                        # Convert with optimized settings
                        img.save(webp_path, "WEBP", quality=95, method=6, optimize=True)
                        # No explicit img.close() needed

                # Verify conversion was successful
                if not os.path.exists(webp_path):
                    self.logger.error(f"WebP conversion failed - output file not created: {webp_path}")
                    return None

                # Verify output file is valid and non-empty
                if os.path.getsize(webp_path) == 0:
                    self.logger.error(f"WebP conversion failed - output file is empty: {webp_path}")
                    self._safe_remove_file(webp_path)
                    return None

                # Clean up original file after successful conversion
                self._safe_remove_file(image_path)

                self.logger.debug(f"Successfully converted to WebP: {image_path} -> {webp_path}")
                return webp_path

            except (Image.DecompressionBombError, Image.DecompressionBombWarning) as e:
                self.logger.error(f"Image too large or potentially malicious: {image_path} - {e}")
                self._safe_remove_file(webp_path)  # Clean up any partial output
                return None
            except MemoryError as e:
                self.logger.error(f"Insufficient memory to process image: {image_path} - {e}")
                self._safe_remove_file(webp_path)  # Clean up any partial output
                return None
            except Exception as e:
                self.logger.error(f"Failed to convert {image_path}: {e}")
                self._safe_remove_file(webp_path)  # Clean up any partial output
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to convert {image_path}: {e}")
            return None

    def copy_local_image(self, local_image_path: str) -> Optional[str]:
        """
        Copy a local image (already on disk) to self.images_dir with enhanced memory management.
        Return the path to the newly-copied image, or None if it doesn't exist.
        """
        if not os.path.exists(local_image_path):
            return None

        # Validate and sanitize filename to prevent path traversal
        base_image_name = os.path.basename(local_image_path)
        # Remove directory traversal sequences and invalid characters
        base_image_name = os.path.basename(os.path.normpath(base_image_name))
        if '..' in base_image_name or '/' in base_image_name or '\\' in base_image_name:
            # Generate safe filename from path hash if suspicious
            base_image_name = hashlib.md5(local_image_path.encode()).hexdigest() + os.path.splitext(base_image_name)[1]

        base_dest_path = os.path.join(self.images_dir, base_image_name)
        base_webp_path = base_dest_path.rsplit('.', 1)[0] + '.webp'

        # Verify the final path is within images_dir
        if not os.path.abspath(base_dest_path).startswith(os.path.abspath(self.images_dir)):
            raise ValueError(f"Path traversal attempt detected: {base_image_name}")

        # Caching: Check for WebP version FIRST before making filename unique
        if os.path.exists(base_webp_path):
            self.logger.info(f"Using cached WebP image: {base_webp_path}")
            return base_webp_path

        # If not cached, make filename unique if needed
        image_name = self._make_filename_unique(base_image_name, self.images_dir)
        dest_path = os.path.join(self.images_dir, image_name)

        # Only copy if not already present
        if not os.path.exists(dest_path):
            try:
                # Enhanced memory management: Check file size before copying
                file_size = os.path.getsize(local_image_path)
                max_size = 50 * 1024 * 1024  # 50MB limit for local files
                if file_size > max_size:
                    self.logger.warning(f"Local image too large: {local_image_path} ({file_size} bytes, max {max_size})")
                    return None

                # Use shutil.copy2 for efficient copying with metadata preservation
                shutil.copy2(local_image_path, dest_path)
                self.logger.debug(f"Copied local image: {local_image_path} -> {dest_path} ({file_size} bytes)")

            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to copy image {local_image_path}: {e}")
                # Clean up any partial copy
                self._safe_remove_file(dest_path)
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error copying image {local_image_path}: {e}")
                # Clean up any partial copy
                self._safe_remove_file(dest_path)
                return None

        return dest_path

    def process_images(self, content: str, markdown_file_path: Optional[str] = None) -> Tuple[str, int, int]:
        """
        Find image references (Markdown, <img>, <a href>, srcset), including local/relative paths.
        Download/copy them to images_dir, convert to .webp, then update references in content.
        Return (updated_content, images_converted_count, images_cached_count).
        """
        self.logger.info("FileProcessor.process_images is running")

        # Markdown images: ![alt](url)
        markdown_image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)
        html_image_urls = re.findall(r'<img\s+[^>]*src="([^"]+)"', content)
        href_urls = re.findall(r'<a\s+[^>]*href="([^"]+)"', content)
        srcset_urls = re.findall(r'srcset="([^"]+)"', content)
        all_srcset_urls = []
        for s in srcset_urls:
            urls_in_srcset = re.findall(r'([^\s,]+)', s)
            all_srcset_urls.extend(urls_in_srcset)

        image_urls = set(markdown_image_urls + html_image_urls + href_urls + all_srcset_urls)
        local_image_paths = {}
        images_converted = 0
        images_cached = 0
        
        # Track which images we've already processed in THIS run to avoid double-counting
        processed_urls = set()

        # Enhanced memory management: Process images with resource monitoring
        total_images = len(image_urls)
        processed_count = 0

        for url in image_urls:
            processed_count += 1
            self.logger.debug(f"Processing image {processed_count}/{total_images}: {url}")

            # Skip if we've already processed this URL in this run
            if url in processed_urls:
                # Find the existing path for this URL
                if url in local_image_paths:
                    continue
                    
            processed_urls.add(url)

            image_path = None
            # Check if URL is local (relative path)
            if not url.startswith('http') and not url.startswith('//'):
                if markdown_file_path:
                    markdown_dir = os.path.dirname(markdown_file_path)
                    # Validate relative path to prevent directory traversal
                    if '..' in url or url.startswith('/'):
                        self.logger.warning(f"Skipping potentially unsafe image path: {url}")
                        continue
                    full_local_path = os.path.join(markdown_dir, url)
                    # Verify the resolved path is within expected directories
                    abs_local_path = os.path.abspath(full_local_path)
                    abs_content_dir = os.path.abspath(self.content_dir)
                    abs_markdown_dir = os.path.abspath(markdown_dir)
                    if not (abs_local_path.startswith(abs_content_dir) or abs_local_path.startswith(abs_markdown_dir)):
                        self.logger.warning(f"Skipping image path outside content directory: {url}")
                        continue
                    image_path = self.copy_local_image(full_local_path)
            else:
                image_path = self.download_image(url, self.images_dir)

            if image_path:
                # Check if the returned path is already a WebP file (cached from previous builds)
                if image_path.endswith('.webp'):
                    webp_path = image_path
                    images_cached += 1  # This was truly cached from a previous build
                    self.logger.debug(f"Using cached WebP from previous build for {url}")
                else:
                    # Convert to WebP (new image in this build)
                    webp_path = self.convert_image_to_webp(image_path)
                    if webp_path:
                        images_converted += 1
                        self.logger.debug(f"Converted new image to WebP for {url}")
                        
                if webp_path:
                    # Sanitize webp filename to prevent path traversal
                    webp_name = os.path.basename(webp_path)
                    webp_name = os.path.basename(os.path.normpath(webp_name))
                    if '..' in webp_name or '/' in webp_name or '\\' in webp_name:
                        # Generate safe filename if suspicious
                        webp_name = hashlib.md5(webp_path.encode()).hexdigest() + '.webp'
                    local_image_paths[url] = f"/images/{webp_name}"

                # Enhanced memory management: Explicit cleanup and garbage collection hints
                # for large image processing batches
                if processed_count % 10 == 0:  # Every 10 images
                    import gc
                    gc.collect()  # Suggest garbage collection for large batches
                    self.logger.debug(f"Memory cleanup after processing {processed_count} images")

        # Replace src, href, and srcset references in content
        for original_url, new_path in local_image_paths.items():
            content = content.replace(f'src="{original_url}"', f'src="{new_path}"')
            content = content.replace(f'href="{original_url}"', f'href="{new_path}"')
            content = content.replace(f']({original_url})', f']({new_path})')
            content = re.sub(f'{re.escape(original_url)}(?=\\s|,|$)', new_path, content)

        return content, images_converted, images_cached

    def parse_markdown_with_metadata(self, filepath: str) -> Tuple[Dict[str, Any], str]:
        """Parse a markdown file with YAML front matter."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to read markdown file {filepath}: {e}")
            return {}, ""

        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError as e:
                self.logger.error(f"Invalid YAML front matter in {filepath}: {e}")
                metadata = {}
            markdown_content = parts[2].strip()
        else:
            metadata = {}
            markdown_content = content

        return metadata, markdown_content

    def format_date(self, date_str: Optional[Union[str, datetime, date]] = None) -> str:
        """Format a date string for display."""
        if date_str is None:
            date_obj = datetime.now()
        else:
            date_obj = self.parse_date(date_str)
        return date_obj.strftime('%B %d, %Y')

    def get_author_name(self, author_id: Union[int, str]) -> str:
        """Get author name from ID."""
        # Handle both string and int author IDs
        if isinstance(author_id, str):
            try:
                author_id = int(author_id)
            except ValueError:
                return str(author_id)  # If it's already a name, return it

        # Get the author value - it could be a string or dict
        author = self.authors.get(author_id)
        if author:
            # If author is a dict with 'name' key, use that
            if isinstance(author, dict) and 'name' in author:
                return author['name']
            # If author is just a string, return it directly
            elif isinstance(author, str):
                return author
            else:
                return str(author)
        return 'Unknown Author'

    def process_featured_image(self, featured_image_path: str, markdown_file_path: Optional[str] = None) -> Optional[str]:
        """
        Process a featured image path, converting it to WebP and returning the absolute path.
        """
        if not featured_image_path:
            return None
            
        # Check if it's a local path (relative to content or absolute within site)
        if not featured_image_path.startswith('http') and not featured_image_path.startswith('//'):
            if markdown_file_path:
                # Get the site root directory (parent of content directory)
                site_root = os.path.dirname(self.content_dir)
                full_local_path = None
                
                # Try multiple common locations for featured images
                search_paths = []
                
                if featured_image_path.startswith('/'):
                    # Absolute path from site root
                    search_paths.append(os.path.join(site_root, featured_image_path.lstrip('/')))
                elif featured_image_path.startswith('assets/') or featured_image_path.startswith('content/'):
                    # Already has directory prefix
                    search_paths.append(os.path.join(site_root, featured_image_path))
                else:
                    # Just a filename - try common locations
                    filename = os.path.basename(featured_image_path)
                    search_paths.extend([
                        os.path.join(site_root, 'assets', 'images', filename),  # Most common
                        os.path.join(site_root, 'assets', filename),
                        os.path.join(self.content_dir, 'posts', filename),
                        os.path.join(self.content_dir, 'pages', filename),
                        os.path.join(self.content_dir, filename),
                        os.path.join(os.path.dirname(markdown_file_path), filename)  # Relative to markdown
                    ])
                
                # Find the first existing file
                for path in search_paths:
                    if os.path.exists(path):
                        full_local_path = path
                        break
                
                if full_local_path:
                    full_local_path = os.path.abspath(full_local_path)
                    
                    # Validate path is safe (allow going to site root but not beyond)
                    if not full_local_path.startswith(os.path.abspath(site_root)):
                        self.logger.warning(f"Skipping potentially unsafe featured image path: {featured_image_path}")
                        return None
                        
                    # Copy and convert the image
                    image_path = self.copy_local_image(full_local_path)
                    if image_path:
                        if image_path.endswith('.webp'):
                            # Already WebP (cached)
                            webp_name = os.path.basename(image_path)
                            return f"/images/{webp_name}"
                        else:
                            # Convert to WebP
                            webp_path = self.convert_image_to_webp(image_path)
                            if webp_path:
                                webp_name = os.path.basename(webp_path)
                                return f"/images/{webp_name}"
                else:
                    self.logger.debug(f"Featured image not found in any location: {featured_image_path}")
        else:
            # Remote URL - download and process
            image_path = self.download_image(featured_image_path, self.images_dir)
            if image_path:
                if image_path.endswith('.webp'):
                    # Already WebP (cached)
                    webp_name = os.path.basename(image_path)
                    return f"/images/{webp_name}"
                else:
                    # Convert to WebP
                    webp_path = self.convert_image_to_webp(image_path)
                    if webp_path:
                        webp_name = os.path.basename(webp_path)
                        return f"/images/{webp_name}"
        
        return None

    def build_post_or_page(self, metadata, html_content, post_slug, output_dir, is_page, markdown_file_path=None):
        """Build a single post or page."""
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, 'index.html')
        title = metadata.get('title', 'Untitled') if isinstance(metadata.get('title'), str) else 'Untitled'
        author_name = self.get_author_name(metadata.get('author', 'Unknown'))
        formatted_date = self.format_date(metadata.get('date'))
        relative_path = self.calculate_relative_path(output_dir)
        template_part = metadata.get('template')
        if template_part:
            template_name = f"post-{template_part}.html" if not is_page else f"page-{template_part}.html"
        else:
            template_name = 'page.html' if is_page else 'post.html'
        
        # Process featured image if present
        processed_featured_image = None
        if metadata.get('featured_image'):
            processed_featured_image = self.process_featured_image(metadata.get('featured_image'), markdown_file_path)
            if processed_featured_image:
                self.logger.debug(f"Processed featured image: {metadata.get('featured_image')} -> {processed_featured_image}")
        
        try:
            template = self.env.get_template(template_name)

            # Compute categories and tags
            post_categories = []
            for cat_id in metadata.get('categories', []):
                if isinstance(cat_id, int):
                    category = self.categories.get(cat_id, {})
                    if isinstance(category, dict):
                        post_categories.append(category.get('name', f"Unknown (ID: {cat_id})"))
                    elif isinstance(category, str):
                        post_categories.append(category)

            post_tags = []
            for tag_id in metadata.get('tags', []):
                if isinstance(tag_id, int):
                    tag = self.tags.get(tag_id, {})
                    post_tags.append(tag.get('name', f"Unknown (ID: {tag_id})"))

            rendered_html = template.render(
                content=html_content,
                title=title,
                author=author_name,
                date=formatted_date,
                categories=post_categories,
                tags=post_tags,
                featured_image=processed_featured_image or metadata.get('featured_image', None),
                seo_title=metadata.get('seo_title', title),
                seo_keywords=metadata.get('keywords', ''),
                seo_description=metadata.get('description', ''),
                lang=metadata.get('lang', 'en'),
                pages=self.pages,
                relative_path=relative_path,
                metadata=metadata,
                page=metadata,
                site_url=self.site_url,
                get_author_name=self.get_author_name
            )
            try:
                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(rendered_html)
                self.logger.debug(f"Generated HTML: {output_file_path}")
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to write HTML file {output_file_path}: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error writing HTML file {output_file_path}: {e}")
                return False

            return True
        except (TemplateNotFound, TemplateSyntaxError) as e:
            self.logger.error(f"Template error for {post_slug}: {e}")
            return False

    def generate_excerpt(self, content):
        """Generate an excerpt from content."""
        # First, convert markdown to HTML to extract plain text properly
        html_content = self.markdown_filter(content)
        
        # Strip HTML tags to get plain text
        plain_text = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up extra whitespace
        plain_text = ' '.join(plain_text.split())
        
        # Extract first 30 words
        words = plain_text.split()
        if len(words) > 30:
            excerpt_text = ' '.join(words[:30]) + '...'
        else:
            excerpt_text = plain_text
        
        # Return as plain text wrapped in paragraph tags
        return f"<p>{excerpt_text}</p>"

    def process(self, file_path, is_page):
        """Process a single markdown file."""
        try:
            metadata, markdown_content = self.parse_markdown_with_metadata(file_path)

            # Process images in the content
            processed_content, images_converted, images_cached = self.process_images(markdown_content, file_path)

            # Convert to HTML
            html_content = self.markdown_filter(processed_content)

            # Determine slug and output directory
            slug = metadata.get('custom_url', os.path.splitext(os.path.basename(file_path))[0])

            # Determine output directory for posts and pages
            if is_page:
                output_dir = os.path.join(self.output_dir, slug)
            else:
                # If blog_slug is empty, put posts at root; else, under blog_slug
                if self.blog_slug:
                    output_dir = os.path.join(self.output_dir, self.blog_slug, slug)
                else:
                    output_dir = os.path.join(self.output_dir, slug)

            # Build the post or page
            success = self.build_post_or_page(metadata, html_content, slug, output_dir, is_page, file_path)

            # Return simple format like original stattic.py for performance
            if is_page:
                # Pages do not produce post_metadata
                return {"post_metadata": None, "images_converted": images_converted, "images_cached": images_cached}
            else:
                # Prepare metadata for the main index page
                # If blog_slug is empty, permalink is just slug; else, blog_slug/slug
                if self.blog_slug:
                    permalink = f"{self.blog_slug}/{slug}/"
                else:
                    permalink = f"{slug}/"
                raw_date = metadata.get('date')

                # Process excerpt - convert markdown to HTML in all cases
                if metadata.get('excerpt'):
                    # If excerpt is from metadata, convert markdown to HTML
                    excerpt_html = self.markdown_filter(metadata.get('excerpt'))
                else:
                    # If excerpt is generated from content, it's already converted in generate_excerpt
                    excerpt_html = self.generate_excerpt(processed_content)

                # Process featured image for blog listing metadata
                processed_featured_image_for_listing = None
                if metadata.get('featured_image'):
                    processed_featured_image_for_listing = self.process_featured_image(metadata.get('featured_image'), file_path)

                # Update metadata with processed featured image for blog listings
                metadata_for_listing = metadata.copy()
                if processed_featured_image_for_listing:
                    metadata_for_listing['featured_image'] = processed_featured_image_for_listing

                post_meta = {
                    'title': metadata.get('title', 'Untitled'),
                    'excerpt': excerpt_html,
                    'permalink': permalink,
                    'date': self.format_date(raw_date),  # Formatted date for display
                    'raw_date': raw_date,  # Raw date for sitemap and sorting
                    'metadata': metadata_for_listing  # Use updated metadata with processed featured image
                }
                return {"post_metadata": post_meta, "images_converted": images_converted, "images_cached": images_cached}
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return {"post_metadata": None, "images_converted": 0, "images_cached": 0}

    def calculate_relative_path(self, current_output_dir: str) -> str:
        """Calculate relative path from current directory to root."""
        rel_path = os.path.relpath(self.output_dir, current_output_dir)
        # Ensure relative path ends with '/' for proper asset linking
        if rel_path == '.':
            return ''
        else:
            return rel_path + '/'

class InfoFilter(logging.Filter):
    """Filter to allow only selected INFO messages to be shown in the console."""
    def filter(self, record: logging.LogRecord) -> bool:
        allowed_messages = [
            "Site build completed in",
            "Total posts generated:",
            "Total pages generated:",
            "Total images converted to WebP:",
            "Total images reused from cache:",
            "Building blog page with pagination",
            "Building index page",
            "Generating RSS feed",
            "Generating XML sitemap",
            "Generating robots.txt",
            "Generating llms.txt",
            "Building 404 page"
        ]
        return any(msg in record.getMessage() for msg in allowed_messages)

def site_title_from_url(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "")
    return domain

class Stattic:
    def create_markdown_parser(self) -> Any:
        """Create a Mistune markdown parser with a custom renderer."""
        class CustomRenderer(mistune.HTMLRenderer):
            def __init__(self) -> None:
                super().__init__(escape=False)
            def block_code(self, code: str, info: Optional[str] = None) -> str:
                escaped_code = mistune.escape(code)
                return '<pre style="white-space: pre-wrap;"><code>{}</code></pre>'.format(escaped_code)
        return mistune.create_markdown(
            renderer=CustomRenderer(),
            plugins=['table', 'task_lists', 'strikethrough']
        )

    def markdown_filter(self, text: str) -> str:
        """Convert markdown text to HTML."""
        return self.markdown_parser(text)

    def __init__(
        self, 
        content_dir: str = 'content', 
        templates_dir: str = 'templates', 
        output_dir: str = 'output', 
        posts_per_page: int = 5, 
        sort_by: str = 'date', 
        fonts: Optional[List[str]] = None, 
        site_url: Optional[str] = None, 
        assets_dir: Optional[str] = None, 
        blog_slug: str = 'blog', 
        site_title: Optional[str] = None, 
        site_tagline: Optional[str] = None
    ) -> None:
        self.content_dir = content_dir
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.posts_per_page = posts_per_page
        self.sort_by = sort_by
        self.fonts = fonts or ['Quicksand']
        self.site_url = site_url
        self.assets_dir = assets_dir
        self.blog_slug = blog_slug
        self.site_title = site_title
        self.site_tagline = site_tagline
        self.posts_generated = 0
        self.pages_generated = 0
        self.image_conversion_count = 0
        self.image_cache_count = 0
        self.posts = []  # Collect post metadata during processing

        # Initialize Jinja2 environment and markdown parser FIRST
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.markdown_parser = self.create_markdown_parser()

        # Initialize URL validation and safe requesting
        self.url_validator = URLValidator()
        self.session = requests.Session()
        self.safe_requestor = SafeRequestor(self.url_validator, self.session)

        # If templates_dir is relative and doesn't exist, try to use package templates
        if not os.path.isabs(self.templates_dir) and not os.path.exists(self.templates_dir):
            try:
                package_templates = pkg_resources.resource_filename('stattic_pkg', 'templates')
                if os.path.exists(package_templates):
                    self.templates_dir = package_templates
                    # Re-initialize env with new templates_dir
                    self.env = Environment(loader=FileSystemLoader(self.templates_dir))
            except:
                pass

        self.setup_logging()
        self.create_output_dir()

        # Initialize directories
        self.images_dir = os.path.join(self.output_dir, 'images')
        os.makedirs(self.images_dir, exist_ok=True)

        # Load data
        self.categories = self.load_categories_and_tags('categories')
        self.tags = self.load_categories_and_tags('tags')
        self.authors = self.load_authors()
        self.pages = []
        self.load_pages()

        # Collect posts for blog page regardless of blog_slug
        self.blog_posts = []

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        self.logger = logging.getLogger('Stattic')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            # Console handler with filter
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.addFilter(InfoFilter())
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler for all logs
            logs_dir = os.path.join(os.getcwd(), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            log_filename = datetime.now().strftime('stattic_%Y-%m-%d_%H-%M-%S.log')
            log_filepath = os.path.join(logs_dir, log_filename)

            file_handler = logging.FileHandler(log_filepath)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def minify_assets(self) -> None:
        """Minify CSS and JS assets."""
        assets_output_dir = os.path.join(self.output_dir, 'assets')

        # Minify CSS files
        css_dir = os.path.join(assets_output_dir, 'css')
        if os.path.exists(css_dir):
            for file in os.listdir(css_dir):
                if file.endswith('.css') and not file.endswith('.min.css'):
                    css_path = os.path.join(css_dir, file)
                    try:
                        with open(css_path, 'r', encoding='utf-8') as f:
                            css_content = f.read()
                        minified_css = csscompressor.compress(css_content)
                        minified_path = os.path.join(css_dir, file.replace('.css', '.min.css'))
                        with open(minified_path, 'w', encoding='utf-8') as f:
                            f.write(minified_css)
                        self.logger.debug(f"Minified CSS: {file}")
                    except (IOError, OSError, PermissionError) as e:
                        self.logger.error(f"Failed to minify CSS file {file}: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error minifying CSS file {file}: {e}")

        # Minify JS files
        js_dir = os.path.join(assets_output_dir, 'js')
        if os.path.exists(js_dir):
            for file in os.listdir(js_dir):
                if file.endswith('.js') and not file.endswith('.min.js'):
                    js_path = os.path.join(js_dir, file)
                    try:
                        with open(js_path, 'r', encoding='utf-8') as f:
                            js_content = f.read()
                        minified_js = rjsmin.jsmin(js_content)
                        minified_path = os.path.join(js_dir, file.replace('.js', '.min.js'))
                        with open(minified_path, 'w', encoding='utf-8') as f:
                            f.write(minified_js)
                        self.logger.debug(f"Minified JS: {file}")
                    except (IOError, OSError, PermissionError) as e:
                        self.logger.error(f"Failed to minify JS file {file}: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error minifying JS file {file}: {e}")

    def load_categories_and_tags(self, type_name: str) -> Dict[int, Any]:
        """Load categories or tags from YAML file."""
        file_path = os.path.join(self.content_dir, f'{type_name}.yml')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to read {type_name} file {file_path}: {e}")
                return {}
            except yaml.YAMLError as e:
                self.logger.error(f"Invalid YAML in {type_name} file {file_path}: {e}")
                return {}
        return {}

    def load_authors(self) -> Dict[int, Any]:
        """Load authors from YAML file."""
        file_path = os.path.join(self.content_dir, 'authors.yml')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to read authors file {file_path}: {e}")
                return {}
            except yaml.YAMLError as e:
                self.logger.error(f"Invalid YAML in authors file {file_path}: {e}")
                return {}
        return {}

    def get_author_name(self, author_id: Union[int, str]) -> str:
        """Get author name from ID."""
        # Handle both string and int author IDs
        if isinstance(author_id, str):
            try:
                author_id = int(author_id)
            except ValueError:
                return str(author_id)  # If it's already a name, return it

        # Get the author value - it could be a string or dict
        author = self.authors.get(author_id)
        if author:
            # If author is a dict with 'name' key, use that
            if isinstance(author, dict) and 'name' in author:
                return author['name']
            # If author is just a string, return it directly
            elif isinstance(author, str):
                return author
            else:
                return str(author)
        return 'Unknown Author'

    def load_pages(self) -> None:
        """Load static pages metadata."""
        pages_dir = os.path.join(self.content_dir, 'pages')
        if os.path.exists(pages_dir):
            for file in os.listdir(pages_dir):
                if file.endswith('.md'):
                    file_path = os.path.join(pages_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        slug = metadata.get('custom_url', os.path.splitext(file)[0])

                        # Add permalink for navigation
                        metadata['permalink'] = f"/{slug}/"

                        # Add page metadata to self.pages list
                        self.pages.append(metadata)

    def download_fonts(self) -> None:
        """Download Google Fonts if specified with SSRF protection."""
        if not self.fonts:
            return

        fonts_dir = os.path.join(self.output_dir, 'assets', 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)

        for font in self.fonts:
            font_name = font.replace(' ', '+')
            font_url = GOOGLE_FONTS_API.format(font_name=font_name, weights='400;700')

            try:
                # Validate Google Fonts URL with SSRF protection
                success, result = self.safe_requestor.safe_google_fonts_get(font_url, timeout=30, allow_redirects=True)
                if not success:
                    self.logger.error(f"Failed to download font {font}: {result}")
                    continue

                response = result
                font_css_path = os.path.join(fonts_dir, f'{font.replace(" ", "_").lower()}.css')
                try:
                    with open(font_css_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    self.logger.debug(f"Downloaded font: {font}")
                except (IOError, OSError, PermissionError) as e:
                    self.logger.error(f"Failed to write font CSS file {font_css_path}: {e}")
                    continue
            except Exception as e:
                self.logger.error(f"Unexpected error downloading font {font}: {e}")
                continue

    def download_google_fonts(self) -> None:
        """Download Google Fonts and generate fonts.css file."""
        if not self.fonts:
            # Default to Quicksand if no fonts provided
            self.fonts = ['Quicksand']

        # Check if fonts were preserved from previous build
        if getattr(self, '_fonts_cached', False):
            self.logger.debug("Fonts preserved from cache, skipping download")
            return

        # Create fonts directory
        fonts_dir = os.path.join(self.output_dir, 'assets', 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)

        fonts_css_path = os.path.join(self.output_dir, 'assets', 'css', 'fonts.css')
        os.makedirs(os.path.dirname(fonts_css_path), exist_ok=True)

        # Double-check if fonts are already cached (in case something changed)
        if self._fonts_are_cached(fonts_css_path, fonts_dir):
            self.logger.debug("Fonts already cached, skipping download")
            return

        css_content = "/* Google Fonts - Downloaded for offline use */\n\n"

        # Standard Google Font weights
        font_weights = [300, 400, 700]  # Download light, regular and bold

        for font in self.fonts:
            try:
                # Clean font name for API and filenames
                font_cleaned = font.strip().replace(' ', '+')
                font_slug = font.strip().lower().replace(' ', '-')

                self.logger.info(f"Downloading font: {font}")

                for weight in font_weights:
                    # Define local filenames - use .woff for broader compatibility
                    woff_name = f"{font_slug}-{weight}.woff"
                    woff_path = os.path.join(fonts_dir, woff_name)

                    # Only download if file doesn't exist or is empty (caching)
                    if not os.path.exists(woff_path) or os.path.getsize(woff_path) == 0:
                        # Build the Google Fonts CSS2 API URL
                        google_font_url = f'https://fonts.googleapis.com/css2?family={font_cleaned}:wght@{weight}&display=swap'

                        # Create a custom headers dict for this request to get simpler font response
                        custom_headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }

                        # Fetch the CSS with SSRF protection
                        success, result = self.safe_requestor.safe_google_fonts_get(google_font_url, timeout=30, allow_redirects=True, headers=custom_headers)
                        if not success:
                            self.logger.warning(f"Failed to fetch Google Fonts CSS {google_font_url}: {result}")
                            continue

                        response = result
                        css_data = response.text
                        self.logger.debug(f"Received font CSS for {font} weight {weight}: {len(css_data)} chars")

                        # Extract font file URLs - look for the main latin font file
                        font_urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css_data)
                        if not font_urls:
                            self.logger.warning(f"No font URLs found in CSS for {font} weight {weight}")
                            continue

                        # Download the font file - prioritize the last one (usually the main latin charset)
                        font_url = font_urls[-1]  # Last URL is typically the main latin font
                        self.logger.debug(f"Downloading font file: {font_url}")
                        
                        # Validate and download font file with SSRF protection
                        success, result = self.safe_requestor.safe_google_fonts_get(font_url, timeout=30, allow_redirects=True)
                        if success:
                            font_response = result
                            try:
                                # Verify we got actual font data
                                if len(font_response.content) < 1000:  # Font files should be at least 1KB
                                    self.logger.warning(f"Font file too small ({len(font_response.content)} bytes) for {font} weight {weight}")
                                    continue
                                    
                                with open(woff_path, 'wb') as f:
                                    f.write(font_response.content)
                                self.logger.info(f"Downloaded {font} weight {weight} → {woff_name} ({len(font_response.content)} bytes)")
                            except (IOError, OSError, PermissionError) as e:
                                self.logger.error(f"Failed to write font file {woff_path}: {e}")
                                continue
                        else:
                            self.logger.warning(f"Failed to download font file {font_url}: {result}")
                            continue

                    # Generate @font-face CSS rule (only if the font file exists)
                    if os.path.exists(woff_path) and os.path.getsize(woff_path) > 1000:  # Ensure file is substantial
                        # Determine format based on file extension
                        if woff_path.endswith('.woff2'):
                            font_format = 'woff2'
                        elif woff_path.endswith('.woff'):
                            font_format = 'woff'
                        else:
                            font_format = 'truetype'
                            
                        css_content += f"""@font-face {{
    font-family: '{font.strip()}';
    font-style: normal;
    font-weight: {weight};
    font-display: swap;
    src: url('../fonts/{woff_name}') format('{font_format}');
}}

"""

            except Exception as e:
                self.logger.warning(f"Failed to download font {font}: {e}")

        # Add font-family rules based on font assignment logic
        if self.fonts:
            title_font = self.fonts[0].strip()  # First font for titles/headings
            body_font = self.fonts[1].strip() if len(self.fonts) > 1 else self.fonts[0].strip()  # Second font for body, or same if only one
            
            css_content += f"""
/* Font assignments */
body {{
    font-family: '{body_font}', sans-serif;
}}

h1, h2, h3, h4, h5, h6, .title-font {{
    font-family: '{title_font}', sans-serif;
}}

/* Semantic font classes */
.font-body-light {{
    font-family: '{body_font}', sans-serif;
    font-weight: 300;
}}

.font-body {{
    font-family: '{body_font}', sans-serif;
    font-weight: 400;
}}

.font-body-bold {{
    font-family: '{body_font}', sans-serif;
    font-weight: 700;
}}

.font-heading-light {{
    font-family: '{title_font}', sans-serif;
    font-weight: 300;
}}

.font-heading {{
    font-family: '{title_font}', sans-serif;
    font-weight: 400;
}}

.font-heading-bold {{
    font-family: '{title_font}', sans-serif;
    font-weight: 700;
}}

/* Legacy classes for backward compatibility */
.quicksand-300 {{
    font-family: '{title_font}', sans-serif;
    font-weight: 300;
}}

.quicksand-400 {{
    font-family: '{title_font}', sans-serif;
    font-weight: 400;
}}

.quicksand-700 {{
    font-family: '{title_font}', sans-serif;
    font-weight: 700;
}}
"""

        # Write fonts.css file
        try:
            with open(fonts_css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to write fonts CSS file {fonts_css_path}: {e}")
            return False

        self.logger.info(f"Generated fonts.css with {len(self.fonts)} font families")

    def _fonts_are_cached(self, fonts_css_path: str, fonts_dir: str) -> bool:
        """Check if fonts are already cached and CSS file exists."""
        if not os.path.exists(fonts_css_path):
            return False

        # Check if all expected font files exist
        font_weights = [300, 400, 700]  # Match the download weights
        for font in self.fonts:
            font_slug = font.strip().lower().replace(' ', '-')
            for weight in font_weights:
                woff_name = f"{font_slug}-{weight}.woff"
                woff_path = os.path.join(fonts_dir, woff_name)
                if not os.path.exists(woff_path) or os.path.getsize(woff_path) < 1000:  # Font files should be substantial
                    return False

        # Check if CSS file contains references to all current fonts
        try:
            with open(fonts_css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()

            for font in self.fonts:
                if f"font-family: '{font.strip()}'" not in css_content:
                    return False

            return True
        except Exception:
            return False

    def copy_assets_to_output(self) -> None:
        """Copy assets directory to output, preserving cached fonts."""
        output_assets_dir = os.path.join(self.output_dir, 'assets')

        # Check if fonts are cached before clearing anything
        fonts_dir = os.path.join(output_assets_dir, 'fonts')
        fonts_css_path = os.path.join(output_assets_dir, 'css', 'fonts.css')
        fonts_cached = self._fonts_are_cached(fonts_css_path, fonts_dir)

        # Copy assets as normal
        if self.assets_dir and os.path.exists(self.assets_dir):
            try:
                if os.path.exists(output_assets_dir):
                    # If fonts are cached, preserve them during asset copy
                    if fonts_cached:
                        self._copy_assets_preserving_fonts(self.assets_dir, output_assets_dir, fonts_dir, fonts_css_path)
                    else:
                        shutil.rmtree(output_assets_dir)
                        shutil.copytree(self.assets_dir, output_assets_dir)
                else:
                    shutil.copytree(self.assets_dir, output_assets_dir)
                self.logger.info(f"Copied assets from {self.assets_dir}")
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to copy assets from {self.assets_dir}: {e}")
        elif os.path.exists('assets'):
            try:
                if os.path.exists(output_assets_dir):
                    # If fonts are cached, preserve them during asset copy
                    if fonts_cached:
                        self._copy_assets_preserving_fonts('assets', output_assets_dir, fonts_dir, fonts_css_path)
                    else:
                        shutil.rmtree(output_assets_dir)
                        shutil.copytree('assets', output_assets_dir)
                else:
                    shutil.copytree('assets', output_assets_dir)
                self.logger.info("Copied assets from local assets directory")
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to copy assets from local assets directory: {e}")

        # Set flag to indicate if fonts were preserved
        self._fonts_cached = fonts_cached

    def _copy_assets_preserving_fonts(self, source_assets: str, output_assets_dir: str, fonts_dir: str, fonts_css_path: str) -> None:
        """Copy assets while preserving cached fonts."""
        import tempfile

        try:
            # Backup cached fonts
            temp_dir = tempfile.mkdtemp()
            fonts_backup = os.path.join(temp_dir, 'fonts')
            fonts_css_backup = os.path.join(temp_dir, 'fonts.css')

            shutil.copytree(fonts_dir, fonts_backup)
            shutil.copy2(fonts_css_path, fonts_css_backup)

            # Clear and copy assets
            shutil.rmtree(output_assets_dir)
            shutil.copytree(source_assets, output_assets_dir)

            # Restore cached fonts
            fonts_dir_new = os.path.join(output_assets_dir, 'fonts')
            fonts_css_path_new = os.path.join(output_assets_dir, 'css', 'fonts.css')

            # Ensure directories exist
            os.makedirs(fonts_dir_new, exist_ok=True)
            os.makedirs(os.path.dirname(fonts_css_path_new), exist_ok=True)

            # Restore fonts
            if os.path.exists(fonts_dir_new):
                shutil.rmtree(fonts_dir_new)
            shutil.copytree(fonts_backup, fonts_dir_new)
            shutil.copy2(fonts_css_backup, fonts_css_path_new)

            # Cleanup temp directory
            shutil.rmtree(temp_dir)
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to copy assets while preserving fonts: {e}")
            # Cleanup temp directory if it exists
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

    def _clean_assets_preserving_fonts(self, assets_path: str, fonts_dir: str, fonts_css_path: str) -> None:
        """Clean assets directory while preserving cached fonts."""
        import tempfile

        # Backup cached fonts
        temp_dir = tempfile.mkdtemp()
        fonts_backup = os.path.join(temp_dir, 'fonts')
        fonts_css_backup = os.path.join(temp_dir, 'fonts.css')

        try:
            shutil.copytree(fonts_dir, fonts_backup)
            shutil.copy2(fonts_css_path, fonts_css_backup)

            # Remove assets directory
            shutil.rmtree(assets_path)

            # Recreate assets directory structure
            os.makedirs(os.path.join(assets_path, 'fonts'), exist_ok=True)
            os.makedirs(os.path.join(assets_path, 'css'), exist_ok=True)

            # Restore cached fonts
            shutil.copytree(fonts_backup, os.path.join(assets_path, 'fonts'), dirs_exist_ok=True)
            shutil.copy2(fonts_css_backup, os.path.join(assets_path, 'css', 'fonts.css'))

        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to clean assets while preserving fonts: {e}")
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass  # Ignore cleanup errors

    def create_output_dir(self) -> None:
        """Create output directory, preserving non-Stattic files and cached fonts."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            return

        # Define files and directories that Stattic generates
        stattic_generated = {
            # Root files Stattic creates
            'index.html', '404.html', 'sitemap.xml', 'robots.txt', 'llms.txt', 'rss.xml',
            # Directories Stattic creates
            'assets', 'images', self.blog_slug,
            # Legacy feed directory (if it exists)
            'feed'
        }

        # Add page directories (these are generated from content/pages)
        pages_dir = os.path.join(self.content_dir, 'pages')
        if os.path.exists(pages_dir):
            for page_file in os.listdir(pages_dir):
                if page_file.endswith('.md'):
                    # Read the page to get its slug
                    page_path = os.path.join(pages_dir, page_file)
                    try:
                        with open(page_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            metadata = yaml.safe_load(parts[1])
                            slug = metadata.get('custom_url', os.path.splitext(page_file)[0])
                            stattic_generated.add(slug)
                    except Exception:
                        # If we can't read the page, use filename as fallback
                        stattic_generated.add(os.path.splitext(page_file)[0])

        # Check if fonts need to be preserved
        fonts_dir = os.path.join(self.output_dir, 'assets', 'fonts')
        fonts_css_path = os.path.join(self.output_dir, 'assets', 'css', 'fonts.css')
        fonts_to_preserve = self.fonts and self._fonts_are_cached(fonts_css_path, fonts_dir)

        preserved_items = []

        # Remove only Stattic-generated files and directories
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)

            if item in stattic_generated:
                # Special handling for assets directory if fonts need to be preserved
                if item == 'assets' and fonts_to_preserve:
                    self._clean_assets_preserving_fonts(item_path, fonts_dir, fonts_css_path)
                    preserved_items.append('cached fonts')
                # Special handling for images directory to preserve cached WebP files
                elif item == 'images':
                    if os.path.isdir(item_path):
                        # Count existing WebP files before cleanup
                        existing_webp_count = 0
                        if os.path.exists(item_path):
                            existing_webp_count = len([f for f in os.listdir(item_path) if f.endswith('.webp')])
                        
                        # Only remove non-WebP files to preserve image cache
                        if os.path.exists(item_path):
                            for img_file in os.listdir(item_path):
                                img_file_path = os.path.join(item_path, img_file)
                                if not img_file.endswith('.webp'):
                                    if os.path.isfile(img_file_path):
                                        os.remove(img_file_path)
                        
                        if existing_webp_count > 0:
                            preserved_items.append(f'{existing_webp_count} cached images')
                else:
                    # Remove Stattic-generated item
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            else:
                # This is a custom file/directory - preserve it
                if item.startswith('.'):
                    preserved_items.append(item)
                else:
                    preserved_items.append(item)

        # Log what was preserved
        if preserved_items:
            self.logger.info(f"Preserved non-Stattic files: {', '.join(preserved_items)}")

        # Set font cache flag if fonts were preserved
        if fonts_to_preserve:
            self._fonts_cached = True

    def parse_date(self, date_str: Union[str, datetime, date]) -> datetime:
        """
        Parse a date string with enhanced format support and error handling.
        
        Supports 16 different date formats with performance optimization.
        Most common formats are checked first for better performance.
        
        Args:
            date_str: String, datetime, or date object to parse
            
        Returns:
            datetime: Parsed datetime object, or datetime.min if parsing fails
        """
        if isinstance(date_str, datetime):
            return date_str
        elif isinstance(date_str, date):
            return datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, str):
            # Strip whitespace and normalize
            date_str = date_str.strip()
            if not date_str:
                self.logger.warning("Empty date string provided, using minimum date")
                return datetime.min

            # Performance-optimized format list (most common first)
            date_formats = [
                '%Y-%m-%d',           # 2025-06-12 (most common)
                '%Y-%m-%dT%H:%M:%S',  # 2025-06-12T14:30:00 (ISO format)
                '%b %d, %Y',          # Jun 12, 2025 (short month)
                '%B %d, %Y',          # June 12, 2025 (full month)
                '%Y-%m-%d %H:%M:%S',  # 2025-06-12 14:30:00
                '%m/%d/%Y',           # 06/12/2025 (US format)
                '%d/%m/%Y',           # 12/06/2025 (EU format)
                '%Y/%m/%d',           # 2025/06/12 (Asian format)
                '%m-%d-%Y',           # 06-12-2025
                '%d-%m-%Y',           # 12-06-2025
                '%Y.%m.%d',           # 2025.06.12
                '%d.%m.%Y',           # 12.06.2025
                '%b %d %Y',           # Jun 12 2025 (no comma)
                '%B %d %Y',           # June 12 2025 (no comma)
                '%Y-%m-%dT%H:%M:%SZ', # 2025-06-12T14:30:00Z (UTC)
                '%Y-%m-%dT%H:%M:%S.%f' # 2025-06-12T14:30:00.123456 (microseconds)
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, log warning and return minimum date
            self.logger.warning(f"Unable to parse date '{date_str}' with any supported format. Using minimum date as fallback.")
            return datetime.min
        else:
            self.logger.warning(f"Invalid date type: {type(date_str)}. Expected string, date, or datetime.")
            return datetime.min

    def get_markdown_files(self, directory: str) -> List[str]:
        """Get all markdown files from a directory."""
        markdown_files = []
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith('.md'):
                    markdown_files.append(os.path.join(directory, file))
        return markdown_files

    def render_template(self, template_name: str, **context: Any) -> Optional[str]:
        """Render a Jinja2 template."""
        try:
            template = self.env.get_template(template_name)
            # Add get_author_name function to template context
            context['get_author_name'] = self.get_author_name
            return template.render(**context)
        except (TemplateNotFound, TemplateSyntaxError) as e:
            self.logger.error(f"Template error: {e}")
            return None

    def build_posts_and_pages(self) -> None:
        """Build all posts and pages using adaptive processing based on workload size."""
        posts_dir = os.path.join(self.content_dir, 'posts')
        pages_dir = os.path.join(self.content_dir, 'pages')

        post_files = self.get_markdown_files(posts_dir)
        page_files = self.get_markdown_files(pages_dir)

        # Prepare tasks for processing
        tasks = [(file, False) for file in post_files] + [(file, True) for file in page_files]

        if not tasks:
            self.logger.warning("No markdown files found to process.")
            return

        # Use adaptive processing based on file count
        # Based on performance testing, multiprocessing becomes beneficial around 12 files
        total_files = len(tasks)
        if total_files >= 12:
            self.logger.info(f"Using multiprocessing for {total_files} files with {os.cpu_count()} workers")
            self._build_with_multiprocessing(tasks)
        else:
            self.logger.info(f"Using single-threaded processing for {total_files} files")
            self._build_single_threaded(tasks)

    def _build_single_threaded(self, tasks: List[Tuple[str, bool]]) -> None:
        """Build posts and pages using single-threaded processing for small workloads."""
        # Create a local FileProcessor instance for single-threaded processing
        session = requests.Session()
        try:
            # Initialize URL validator and safe requestor for single-threaded processing
            url_validator = URLValidator()
            safe_requestor = SafeRequestor(url_validator, session)
            
            processor = FileProcessor(
                self.templates_dir, self.output_dir, self.images_dir,
                self.categories, self.tags, self.authors, self.pages,
                self.site_url, self.content_dir, self.blog_slug, 
                session=session, safe_requestor=safe_requestor
            )

            for file_path, is_page in tasks:
                try:
                    result = processor.process(file_path, is_page)
                    if result:
                        # Accumulate the images
                        self.image_conversion_count += result.get("images_converted", 0)
                        self.image_cache_count += result.get("images_cached", 0)
                        
                        if is_page:
                            self.pages_generated += 1
                        else:
                            self.posts_generated += 1
                            # If there's post_metadata, store it
                            post_meta = result.get("post_metadata")
                            if post_meta:
                                self.posts.append(post_meta)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
        finally:
            # Ensure session is properly closed to prevent resource leaks
            session.close()

    def _build_with_multiprocessing(self, tasks: List[Tuple[str, bool]]) -> None:
        """Build posts and pages using multiprocessing for large workloads."""
        # Separate posts and pages for two-phase processing like original stattic.py
        post_files = [file_path for file_path, is_page in tasks if not is_page]
        page_files = [file_path for file_path, is_page in tasks if is_page]

        # Use same worker calculation as original: all available CPU cores
        optimal_workers = os.cpu_count()

        with ProcessPoolExecutor(
            max_workers=optimal_workers,
            initializer=initializer,
            initargs=(self.templates_dir, self.output_dir, self.images_dir, 
                     self.categories, self.tags, self.authors, self.pages, 
                     self.site_url, self.content_dir, self.blog_slug)
        ) as executor:
            # Process all posts first (like original)
            if post_files:
                post_futures = {executor.submit(process_file, pf, False): pf for pf in post_files}
                for future in as_completed(post_futures):
                    pf = post_futures[future]
                    try:
                        result = future.result()
                        if result:
                            # Accumulate the images
                            self.image_conversion_count += result.get("images_converted", 0)
                            self.image_cache_count += result.get("images_cached", 0)
                            self.posts_generated += 1
                            # If there's post_metadata, store it
                            post_meta = result.get("post_metadata")
                            if post_meta:
                                self.posts.append(post_meta)
                    except Exception as e:
                        self.logger.error(f"Error building post {pf}: {e}")

            # Process all pages second (like original)  
            if page_files:
                page_futures = {executor.submit(process_file, pg, True): pg for pg in page_files}
                for future in as_completed(page_futures):
                    pg = page_futures[future]
                    try:
                        result = future.result()
                        if result:
                            self.image_conversion_count += result.get("images_converted", 0)
                            self.image_cache_count += result.get("images_cached", 0)
                        self.pages_generated += 1
                    except Exception as e:
                        self.logger.error(f"Error building page {pg}: {e}")

    def build_blog_page(self) -> bool:
        """Build the main blog page (single archive page, not paginated)."""
        
        # Check if there's a dedicated blog page defined in pages
        blog_page_data = None
        for page in self.pages:
            if page.get('custom_url', '') == 'blog':
                blog_page_data = page
                break
        
        # If blog_slug is empty and no dedicated blog page exists, skip creating a separate blog page
        # The posts will be handled by build_index_page instead
        if not self.blog_slug and not blog_page_data:
            self.logger.info("blog_slug is empty and no dedicated blog page found. Posts will appear on index page.")
            return True
            
        # Determine output directory and template based on whether we have a dedicated blog page
        if blog_page_data:
            # Use the dedicated blog page setup
            blog_page_output = os.path.join(self.output_dir, blog_page_data.get('custom_url', 'blog'))
            template_name = 'page-blog.html'
            page_title = blog_page_data.get('title', 'Blog')
            self.logger.info(f"Using dedicated blog page: {blog_page_data.get('custom_url', 'blog')}")
        elif self.blog_slug:
            # Use the blog_slug setup
            blog_page_output = os.path.join(self.output_dir, self.blog_slug)
            
            # Check for custom templates
            has_custom_blog_template = os.path.exists(os.path.join(self.templates_dir, 'page-blog.html'))
            has_custom_home_template = os.path.exists(os.path.join(self.templates_dir, 'page-home.html'))

            if has_custom_blog_template:
                template_name = 'page-blog.html'
            elif not has_custom_home_template:
                # No custom blog or homepage - redirect /blog to /
                redirect_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script>
        // Redirect instantly without rendering anything.
        window.location.replace("/");
    </script>
    <meta name="robots" content="noindex">
    <title>Redirecting ...</title>
</head>
<body>
    <p>If you are not redirected automatically, <a href="/">click here</a>.</p>
</body>
</html>"""
                os.makedirs(blog_page_output, exist_ok=True)
                try:
                    with open(os.path.join(blog_page_output, 'index.html'), 'w') as f:
                        f.write(redirect_html)
                    self.logger.info("No blog/homepage template found. Redirected /blog/ to /.")
                except (IOError, OSError, PermissionError) as e:
                    self.logger.error(f"Failed to write blog redirect page: {e}")
                return True
            else:
                self.logger.warning("Template 'page-blog.html' not found. Falling back to 'page.html'.")
                template_name = 'page.html'
            
            page_title = 'Blog'
        else:
            # Fallback - shouldn't reach here due to the check above
            return True
            
        os.makedirs(blog_page_output, exist_ok=True)

        if self.sort_by == 'order':
            sorted_posts = sorted(self.posts, key=lambda p: p['metadata'].get('order', 1000))
        elif self.sort_by == 'title':
            sorted_posts = sorted(self.posts, key=lambda p: p.get('title', '').lower())
        elif self.sort_by == 'author':
            sorted_posts = sorted(self.posts, key=lambda p: str(p['metadata'].get('author', '')).lower())
        else:
            sorted_posts = sorted(self.posts, key=lambda p: self.parse_date(p.get('date', '')), reverse=True)

        total_posts = len(sorted_posts)
        posts_per_page = self.posts_per_page
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page

        # Create all paginated pages for the blog
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * posts_per_page
            end_idx = start_idx + posts_per_page
            page_posts = sorted_posts[start_idx:end_idx]

            # Determine output directory for each page
            if page_num == 1:
                current_page_output = blog_page_output
            else:
                current_page_output = os.path.join(blog_page_output, 'page', str(page_num))
            
            os.makedirs(current_page_output, exist_ok=True)
            
            pagination_links = self.get_pagination_links(page_num, total_pages)

            # Render the template with the appropriate context
            if blog_page_data:
                # For dedicated blog pages, use the blog page metadata and content
                rendered_html = self.render_template(
                    template_name,
                    content=blog_page_data.get('content', ''),
                    title=page_title,
                    posts=page_posts,
                    pages=self.pages,
                    site_url=self.site_url,
                    metadata=blog_page_data,
                    page=blog_page_data,
                    relative_path=self.calculate_relative_path(current_page_output),
                    total_pages=total_pages,
                    current_page=page_num,
                    page_numbers=pagination_links,
                    get_author_name=self.get_author_name
                )
            else:
                # For regular blog_slug pages
                rendered_html = self.render_template(
                    template_name,
                    posts=page_posts,
                    pages=self.pages,
                    page={'title': page_title},
                    relative_path=self.calculate_relative_path(current_page_output),
                    total_pages=total_pages,
                    current_page=page_num,
                    page_numbers=pagination_links,
                    site_url=self.site_url
                )

            try:
                with open(os.path.join(current_page_output, 'index.html'), 'w') as f:
                    f.write(rendered_html)
                
                # Log the page creation
                if blog_page_data:
                    blog_path = blog_page_data.get('custom_url', 'blog')
                else:
                    blog_path = self.blog_slug
                    
                if page_num == 1:
                    self.logger.info(f"Generated blog archive page at /{blog_path}/index.html")
                else:
                    self.logger.info(f"Generated blog page {page_num} at /{blog_path}/page/{page_num}/index.html")
                    
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to write blog page {page_num}: {e}")
                return False

        return True

    def calculate_relative_path(self, current_output_dir: str) -> str:
        """Calculate relative path from current directory to root."""
        rel_path = os.path.relpath(self.output_dir, current_output_dir)
        # Ensure relative path ends with '/' for proper asset linking
        if rel_path == '.':
            return ''
        else:
            return rel_path + '/'

    def get_pagination_links(self, current_page: int, total_pages: int) -> Dict[str, Any]:
        """Generate pagination links."""
        pagination = {
            'current': current_page,
            'total': total_pages,
            'has_previous': current_page > 1,
            'has_next': current_page < total_pages,
            'previous': current_page - 1 if current_page > 1 else None,
            'next': current_page + 1 if current_page < total_pages else None,
            'pages': []
        }

        # Generate page numbers (show 5 pages around current)
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)

        for page_num in range(start_page, end_page + 1):
            pagination['pages'].append({
                'number': page_num,
                'is_current': page_num == current_page,
                'url': f'page-{page_num}' if page_num > 1 else ''
            })

        return pagination

    def get_pagination_links(self, current_page: int, total_pages: int) -> List[Union[int, str]]:
        """
        Returns a list of page numbers (or ellipses) to display in pagination.
        Always shows page 1 and total_pages.
        Shows two pages before and after the current page.
        Inserts '...' when there is a gap.
        """
        delta = 2  # how many pages to show before and after current page
        links = []

        # Always include first page
        links.append(1)

        # Determine start and end range around current page
        start = max(current_page - delta, 2)
        end = min(current_page + delta, total_pages - 1)

        # Insert ellipsis if there's a gap between 1 and start
        if start > 2:
            links.append('...')

        # Add the range of pages
        links.extend(range(start, end + 1))

        # Insert ellipsis if there's a gap between end and the last page
        if end < total_pages - 1:
            links.append('...')

        # Always include the last page if there's more than one page
        if total_pages > 1:
            links.append(total_pages)

        return links

    def build_index_page(self) -> None:
        """
        Build paginated index pages with numbered pagination that shows ellipses.
        - index.html for page 1
        - page/<n>/index.html for pages 2..n
        """
        if not self.posts:
            self.logger.info("No posts found for index page generation")
            return

        # Parse dates for sorting
        for post in self.posts:
            post['parsed_date'] = self.parse_date(post.get('date', ''))

        # Decide how to sort (by title, author, or date)
        if self.sort_by == 'title':
            sort_key = lambda p: p.get('title', '').lower()
            reverse_sort = False
        elif self.sort_by == 'author':
            def author_lower(p):
                author_id = p['metadata'].get('author', '') if 'metadata' in p else ''
                return str(author_id).lower()
            sort_key = author_lower
            reverse_sort = False
        elif self.sort_by == 'order':
            sort_key = lambda p: p['metadata'].get('order', 1000)
            reverse_sort = False
        else:
            # default: sort by date descending
            sort_key = lambda p: p.get('parsed_date', datetime.min)
            reverse_sort = True

        # Sort all posts
        sorted_posts = sorted(self.posts, key=sort_key, reverse=reverse_sort)

        total_posts = len(sorted_posts)
        posts_per_page = self.posts_per_page
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page  # integer ceiling

        # Loop to build each paginated page
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * posts_per_page
            end_idx = start_idx + posts_per_page
            page_posts = sorted_posts[start_idx:end_idx]

            # Determine output directory for current page
            if page_num == 1:
                page_output_dir = self.output_dir
            else:
                page_output_dir = os.path.join(self.output_dir, 'page', str(page_num))
            os.makedirs(page_output_dir, exist_ok=True)

            # Get truncated pagination links for this page
            pagination_links = self.get_pagination_links(page_num, total_pages)

            # Render the index page template with pagination variables
            html = self.render_template(
                'index.html',
                posts=page_posts,
                pages=self.pages,
                page={'title': 'Home' if page_num == 1 else f'Page {page_num}'},
                relative_path=self.calculate_relative_path(page_output_dir),
                current_page=page_num,
                total_pages=total_pages,
                page_numbers=pagination_links,
                site_url=self.site_url,
                site_title=self.site_title,
                site_tagline=self.site_tagline,
                categories=self.categories,
                tags=self.tags,
                authors=self.authors,
                minify=False
            )

            output_path = os.path.join(page_output_dir, 'index.html')
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.info(f"Generated paginated index page at {output_path}")
            except (IOError, OSError, PermissionError) as e:
                self.logger.error(f"Failed to write paginated index page {output_path}: {e}")

        self.logger.info("Building index page")

    def generate_rss_feed(self, site_url: str, site_name: Optional[str] = None) -> bool:
        """Generate RSS feed."""
        if not site_name:
            site_name = site_title_from_url(site_url)

        if not self.posts:
            return

        # Use already-processed posts data instead of re-reading files
        recent_posts = sorted(self.posts, key=lambda x: self.parse_date(x.get('date', '')), reverse=True)[:20]

        # Generate RSS XML
        rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{escape(site_name)}</title>
<link>{escape(site_url)}</link>
<description>Latest posts from {escape(site_name)}</description>
<lastBuildDate>{formatdate()}</lastBuildDate>
'''

        for post in recent_posts:
            title = escape(post.get('title', 'Untitled'))
            # Use permalink that's already computed
            link = f"{site_url.rstrip('/')}/{post.get('permalink', '')}"

            # Use excerpt if available, otherwise truncate content
            if 'excerpt' in post:
                raw_description = post['excerpt']
            else:
                # Use metadata if available for excerpt generation
                raw_description = post.get('metadata', {}).get('excerpt', post.get('title', 'No excerpt available'))

            # Clean and escape the description for XML
            import html as html_module
            clean_description = html_module.unescape(str(raw_description))
            clean_description = re.sub(r'<.*?>', '', clean_description)  # Remove any HTML tags
            clean_description = re.sub(r'\s+', ' ', clean_description)  # Normalize whitespace
            description = escape(clean_description.strip())

            post_date = self.parse_date(post.get('date', ''))
            pub_date = formatdate(post_date.timestamp()) if post_date != datetime.min else formatdate()

            rss_content += f'''
<item>
<title>{title}</title>
<link>{link}</link>
<description>{description}</description>
<pubDate>{pub_date}</pubDate>
<guid>{link}</guid>
</item>'''

        rss_content += '''
</channel>
</rss>'''

        # Write RSS file to /feed/index.xml for backward compatibility
        rss_output_dir = os.path.join(self.output_dir, 'feed')
        os.makedirs(rss_output_dir, exist_ok=True)
        rss_file = os.path.join(rss_output_dir, 'index.xml')
        try:
            with open(rss_file, 'w', encoding='utf-8') as f:
                f.write(rss_content)
            self.logger.info("Generating RSS feed")
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to write RSS feed file {rss_file}: {e}")
            return False

        return True

    def generate_xml_sitemap(self, site_url: str) -> bool:
        """Generate XML sitemap."""
        # Start sitemap
        sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''

        # Add homepage
        sitemap_content += self.format_xml_sitemap_entry(site_url, datetime.now())

        # Add blog page
        blog_url = f"{site_url.rstrip('/')}/{self.blog_slug}/"
        sitemap_content += self.format_xml_sitemap_entry(blog_url, datetime.now())

        # Add posts using already-processed data
        for post in self.posts:
            post_url = f"{site_url.rstrip('/')}/{post.get('permalink', '')}"
            # Use raw_date if available, otherwise fall back to metadata date or formatted date
            raw_date = post.get('raw_date') or post.get('metadata', {}).get('date') or post.get('date', '')
            post_date = self.parse_date(raw_date)
            sitemap_content += self.format_xml_sitemap_entry(post_url, post_date)

        # Add pages using already-loaded data
        for page in self.pages:
            page_url = f"{site_url.rstrip('/')}{page.get('permalink', '/')}"
            page_date = self.parse_date(page.get('date', datetime.now()))
            sitemap_content += self.format_xml_sitemap_entry(page_url, page_date)

        sitemap_content += '</urlset>'

        # Write sitemap file
        sitemap_file = os.path.join(self.output_dir, 'sitemap.xml')
        try:
            with open(sitemap_file, 'w', encoding='utf-8') as f:
                f.write(sitemap_content)
            self.logger.info("Generating XML sitemap")
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to write sitemap file {sitemap_file}: {e}")
            return False

        return True

    def format_xml_sitemap_entry(self, url: str, lastmod: datetime) -> str:
        """Format a single sitemap entry."""
        return f'''<url>
<loc>{escape(url)}</loc>
<lastmod>{lastmod.strftime('%Y-%m-%d')}</lastmod>
</url>
'''

    def generate_robots_txt(self, mode: str = "public") -> bool:
        """Generate robots.txt file."""
        if mode == "public":
            robots_content = """User-agent: *
Allow: /

Sitemap: {}/sitemap.xml""".format(self.site_url.rstrip('/') if self.site_url else '')
        else:
            robots_content = """User-agent: *
Disallow: /"""

        robots_file = os.path.join(self.output_dir, 'robots.txt')
        try:
            with open(robots_file, 'w', encoding='utf-8') as f:
                f.write(robots_content)
            self.logger.info("Generating robots.txt")
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to write robots.txt file {robots_file}: {e}")
            return False

        return True

    def generate_llms_txt(self, site_title: Optional[str] = None, site_tagline: Optional[str] = None) -> bool:
        """Generate llms.txt file for LLM crawlers."""
        if not site_title and self.site_url:
            site_title = site_title_from_url(self.site_url)

        # Create descriptive title
        if site_title:
            title_line = f"# {site_title} - a Python-based static site generator's demo website"
        else:
            title_line = "# Stattic - a Python-based static site generator's demo website"

        llms_content = f"""{title_line}

This site contains structured content formatted for LLM-friendly consumption.

"""

        # Add blog posts content using already-processed data
        if self.posts:
            llms_content += "## Posts\n"

            # Sort posts by date
            sorted_posts = sorted(self.posts, key=lambda x: self.parse_date(x.get('date', '')), reverse=True)

            # Add each post
            for post in sorted_posts:
                title = post.get('title', 'Untitled')
                permalink = post.get('permalink', '')
                url = f"{self.site_url}/{permalink}"

                # Generate unique ID for the post
                content_hash = abs(hash(title + permalink)) % (10**10)

                llms_content += f"- [{title}]({url}): ID {content_hash}\n"

            llms_content += "\n"  

        # Add pages content using already-loaded data
        if self.pages:
            llms_content += "## Pages\n"

            for page in self.pages:
                title = page.get('title', 'Untitled')
                permalink = page.get('permalink', '/')
                url = f"{self.site_url}{permalink}"

                # Generate unique ID for the page
                content_hash = abs(hash(title + permalink)) % (10**10)

                llms_content += f"- [{title}]({url}): ID {content_hash}\n"

            llms_content += "\n"

        # Add sitemap reference
        llms_content += f"""## Sitemap
{self.site_url}/sitemap.xml
"""

        llms_file = os.path.join(self.output_dir, 'llms.txt')
        try:
            with open(llms_file, 'w', encoding='utf-8') as f:
                f.write(llms_content)
            self.logger.info("Generating llms.txt")
        except (IOError, OSError, PermissionError) as e:
            self.logger.error(f"Failed to write llms.txt file {llms_file}: {e}")
            return False

        return True

    def build_404_page(self) -> None:
        """Build 404 error page."""
        html = self.render_template(
            '404.html',
            relative_path='',
            categories=self.categories,
            tags=self.tags,
            authors=self.authors,
            pages=self.pages,
            site_url=self.site_url,
            site_title=self.site_title,
            site_tagline=self.site_tagline,
            minify=False  # Add default minify setting
        )

        if html:
            output_file = os.path.join(self.output_dir, '404.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

        self.logger.info("Building 404 page")

    def build(self) -> None:
        """Main build process."""
        self.logger.info("Starting site build...")

        # Copy assets (with font preservation logic built-in)
        self.copy_assets_to_output()

        # Download fonts (will skip if cached)
        self.download_google_fonts()

        # Build posts and pages
        self.build_posts_and_pages()

        # Build blog and index pages
        self.build_blog_page()
        self.build_index_page()

        # Build 404 page
        self.build_404_page()

    def __del__(self) -> None:
        """Cleanup method to close session when Stattic instance is destroyed."""
        self.cleanup()

    def cleanup(self) -> None:
        """Cleanup resources (close session, etc.)."""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except:
            pass  # Ignore errors during cleanup
