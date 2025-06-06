"""Tests for FileProcessor class."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stattic import FileProcessor


class TestFileProcessor:
    """Test cases for FileProcessor class."""
    
    def test_init_valid_directories(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test FileProcessor initialization with valid directories."""
        processor = FileProcessor(
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            images_dir=os.path.join(mock_output_dir, 'images'),
            categories={1: {'name': 'Test'}},
            tags={1: {'name': 'test'}},
            authors={1: 'Test Author'},
            pages=[],
            site_url='https://example.com',
            content_dir=mock_content_dir,
            blog_slug='blog'
        )
        
        assert processor.templates_dir.exists()
        assert processor.output_dir.exists()
        assert processor.content_dir.exists()
        assert processor.site_url == 'https://example.com'
        assert processor.blog_slug == 'blog'
    
    def test_init_invalid_templates_dir(self, mock_content_dir, mock_output_dir):
        """Test FileProcessor initialization with invalid templates directory."""
        with pytest.raises(FileNotFoundError, match="Templates directory"):
            FileProcessor(
                templates_dir='/nonexistent',
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
    
    def test_init_invalid_content_dir(self, mock_templates_dir, mock_output_dir):
        """Test FileProcessor initialization with invalid content directory."""
        with pytest.raises(FileNotFoundError, match="Content directory"):
            FileProcessor(
                templates_dir=mock_templates_dir,
                output_dir=mock_output_dir,
                images_dir=os.path.join(mock_output_dir, 'images'),
                categories={},
                tags={},
                authors={},
                pages=[],
                site_url=None,
                content_dir='/nonexistent',
                blog_slug='blog'
            )
    
    def test_parse_date_datetime(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test parse_date with datetime object."""
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
        
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = processor.parse_date(dt)
        assert result == dt
    
    def test_parse_date_string_formats(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test parse_date with various string formats."""
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
        
        test_cases = [
            ('2023-01-01', datetime(2023, 1, 1)),
            ('2023-01-01T12:00:00', datetime(2023, 1, 1, 12, 0, 0)),
            ('Jan 01, 2023', datetime(2023, 1, 1)),
            ('01/01/2023', datetime(2023, 1, 1)),
        ]
        
        for date_str, expected in test_cases:
            result = processor.parse_date(date_str)
            assert result == expected
    
    def test_parse_date_invalid(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test parse_date with invalid input."""
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
        
        result = processor.parse_date('invalid-date')
        assert result == datetime.min
        
        result = processor.parse_date(None)
        assert result == datetime.min
    
    def test_is_safe_url(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test URL safety validation."""
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
        
        # Safe URLs
        assert processor._is_safe_url('https://example.com/image.jpg')
        assert processor._is_safe_url('http://example.com/image.jpg')
        
        # Unsafe URLs
        assert not processor._is_safe_url('ftp://example.com/image.jpg')
        assert not processor._is_safe_url('https://localhost/image.jpg')
        assert not processor._is_safe_url('https://127.0.0.1/image.jpg')
        assert not processor._is_safe_url('invalid-url')
    
    def test_is_valid_image_extension(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test image extension validation."""
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
        
        # Valid extensions
        valid_urls = [
            'image.jpg', 'image.jpeg', 'image.png', 'image.gif',
            'image.webp', 'image.bmp', 'image.tiff', 'image.svg'
        ]
        for url in valid_urls:
            assert processor._is_valid_image_extension(url)
        
        # Invalid extensions
        invalid_urls = ['file.txt', 'file.pdf', 'file.doc', 'file']
        for url in invalid_urls:
            assert not processor._is_valid_image_extension(url)
    
    @patch('requests.Session.get')
    def test_download_image_success(self, mock_get, mock_content_dir, mock_templates_dir, 
                                   mock_output_dir, sample_image_data):
        """Test successful image download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/png', 'content-length': '1000'}
        mock_response.iter_content.return_value = [sample_image_data]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
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
        
        result = processor.download_image(
            'https://example.com/test.png',
            os.path.join(mock_output_dir, 'images')
        )
        
        assert result is not None
        assert os.path.exists(result)
    
    def test_download_image_unsafe_url(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test download_image with unsafe URL."""
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
        
        result = processor.download_image(
            'https://localhost/test.png',
            os.path.join(mock_output_dir, 'images')
        )
        
        assert result is None
