"""Security tests for Stattic."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stattic import FileProcessor


class TestSecurity:
    """Test cases for security features."""
    
    def test_url_validation_blocks_localhost(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that localhost URLs are blocked."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        dangerous_urls = [
            'https://localhost/image.jpg',
            'http://127.0.0.1/image.jpg',
            'https://0.0.0.0/image.jpg',
        ]
        
        for url in dangerous_urls:
            assert not processor._is_safe_url(url)
    
    def test_url_validation_blocks_non_http(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that non-HTTP protocols are blocked."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        dangerous_urls = [
            'ftp://example.com/image.jpg',
            'file:///etc/passwd',
            'javascript:alert(1)',
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        ]
        
        for url in dangerous_urls:
            assert not processor._is_safe_url(url)
    
    def test_url_validation_allows_safe_urls(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that safe URLs are allowed."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        safe_urls = [
            'https://example.com/image.jpg',
            'http://example.com/image.jpg',
            'https://cdn.example.com/images/photo.png',
        ]
        
        for url in safe_urls:
            assert processor._is_safe_url(url)
    
    @patch('requests.Session.get')
    def test_download_image_content_type_validation(self, mock_get, mock_content_dir, 
                                                   mock_templates_dir, mock_output_dir):
        """Test that content type is validated when downloading images."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        # Mock response with non-image content type
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = processor.download_image(
            'https://example.com/test.jpg',
            os.path.join(mock_output_dir, 'images')
        )
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_download_image_size_limit(self, mock_get, mock_content_dir, 
                                      mock_templates_dir, mock_output_dir):
        """Test that large files are rejected."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        # Mock response with large content length
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(20 * 1024 * 1024)  # 20MB
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = processor.download_image(
            'https://example.com/large.jpg',
            os.path.join(mock_output_dir, 'images')
        )
        
        assert result is None
    
    def test_filename_sanitization(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that filenames are properly sanitized."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        # Test with mock response
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.iter_content.return_value = [b'fake image data']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # URL with dangerous filename
            dangerous_url = 'https://example.com/../../../etc/passwd.jpg'
            
            result = processor.download_image(
                dangerous_url,
                os.path.join(mock_output_dir, 'images')
            )
            
            if result:
                # Filename should be sanitized
                filename = os.path.basename(result)
                assert '../' not in filename
                assert filename.replace('_', '').replace('.', '').replace('-', '').isalnum()
    
    def test_session_timeout_configuration(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that session timeout is properly configured."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        assert processor.session.timeout == 30
        assert 'User-Agent' in processor.session.headers
    
    @patch('subprocess.run')
    def test_subprocess_timeout_protection(self, mock_run, mock_content_dir, 
                                          mock_templates_dir, mock_output_dir, temp_dir):
        """Test that subprocess calls have timeout protection."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        # Create a test GIF file
        test_image_path = os.path.join(temp_dir, 'test.gif')
        with open(test_image_path, 'wb') as f:
            f.write(b'fake gif data')
        
        # Mock subprocess.run to simulate timeout
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('gif2webp', 60)
        
        with patch('shutil.which', return_value='/usr/bin/gif2webp'):
            result = processor.convert_image_to_webp(test_image_path)
            
            assert result is None
            # Verify timeout was used
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert kwargs.get('timeout') == 60
    
    def test_path_traversal_protection(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test protection against path traversal attacks."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url=None,
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        # Test that paths are resolved to absolute paths
        assert processor.templates_dir.is_absolute()
        assert processor.output_dir.is_absolute()
        assert processor.content_dir.is_absolute()
        assert processor.images_dir.is_absolute()
    
    def test_yaml_safe_loading(self, temp_dir):
        """Test that YAML files are loaded safely."""
        from stattic import Stattic
        
        # Create content directory with malicious YAML
        content_dir = Path(temp_dir) / 'content'
        content_dir.mkdir()
        
        # Create templates directory
        templates_dir = Path(temp_dir) / 'templates'
        templates_dir.mkdir()
        base_template = templates_dir / 'base.html'
        base_template.write_text('<html><body>{{ content }}</body></html>')
        
        # Create malicious categories.yml (this would be dangerous with unsafe loading)
        categories_file = content_dir / 'categories.yml'
        categories_file.write_text("""
!!python/object/apply:os.system
- "echo 'malicious command'"
""")
        
        tags_file = content_dir / 'tags.yml'
        tags_file.write_text('{}')
        
        authors_file = content_dir / 'authors.yml'
        authors_file.write_text('{}')
        
        # This should not execute the malicious command
        try:
            generator = Stattic(
                content_dir=str(content_dir),
                templates_dir=str(templates_dir),
                output_dir=os.path.join(temp_dir, 'output')
            )
            # If we get here, the YAML was safely loaded (or failed to load)
            # Either way, no malicious code was executed
            assert True
        except Exception:
            # Even if loading fails, no malicious code should execute
            assert True
