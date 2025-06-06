"""Tests for image processing functionality."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stattic import FileProcessor


class TestImageProcessing:
    """Test cases for image processing functionality."""
    
    def create_test_image(self, format='PNG', size=(100, 100)):
        """Create a test image in memory."""
        img = Image.new('RGB', size, color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    def test_convert_image_to_webp_png(self, mock_content_dir, mock_templates_dir, mock_output_dir, temp_dir):
        """Test converting PNG image to WebP."""
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
        
        # Create a test PNG image
        test_image_path = os.path.join(temp_dir, 'test.png')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')
        
        result = processor.convert_image_to_webp(test_image_path)
        
        assert result is not None
        assert result.endswith('.webp')
        assert os.path.exists(result)
        assert not os.path.exists(test_image_path)  # Original should be removed
    
    def test_convert_image_to_webp_nonexistent(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test converting non-existent image."""
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
        
        result = processor.convert_image_to_webp('/nonexistent/image.png')
        assert result is None
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_convert_gif_to_webp_with_gif2webp(self, mock_run, mock_which, 
                                              mock_content_dir, mock_templates_dir, 
                                              mock_output_dir, temp_dir):
        """Test converting GIF to WebP using gif2webp."""
        mock_which.return_value = '/usr/bin/gif2webp'
        mock_run.return_value = Mock(returncode=0)
        
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
        
        # Create a test GIF image (actually PNG for simplicity)
        test_image_path = os.path.join(temp_dir, 'test.gif')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')  # Save as PNG but with .gif extension
        
        # Create expected WebP output file
        webp_path = test_image_path.replace('.gif', '.webp')
        with open(webp_path, 'wb') as f:
            f.write(b'fake webp data')
        
        result = processor.convert_image_to_webp(test_image_path)
        
        assert result is not None
        assert result.endswith('.webp')
        mock_run.assert_called_once()
    
    @patch('shutil.which')
    def test_convert_gif_to_webp_fallback_to_pillow(self, mock_which, 
                                                   mock_content_dir, mock_templates_dir, 
                                                   mock_output_dir, temp_dir):
        """Test GIF conversion fallback to Pillow when gif2webp not available."""
        mock_which.return_value = None  # gif2webp not found
        
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
        
        # Create a test GIF image
        test_image_path = os.path.join(temp_dir, 'test.gif')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')  # Save as PNG but with .gif extension
        
        result = processor.convert_image_to_webp(test_image_path)
        
        assert result is not None
        assert result.endswith('.webp')
        assert os.path.exists(result)
    
    def test_convert_rgba_to_webp(self, mock_content_dir, mock_templates_dir, mock_output_dir, temp_dir):
        """Test converting RGBA image to WebP."""
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
        
        # Create a test RGBA image
        test_image_path = os.path.join(temp_dir, 'test.png')
        img = Image.new('RGBA', (10, 10), color=(255, 0, 0, 128))
        img.save(test_image_path, 'PNG')
        
        result = processor.convert_image_to_webp(test_image_path)
        
        assert result is not None
        assert result.endswith('.webp')
        assert os.path.exists(result)
    
    def test_copy_local_image(self, mock_content_dir, mock_templates_dir, mock_output_dir, temp_dir):
        """Test copying local image to images directory."""
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
        
        # Create a test image
        test_image_path = os.path.join(temp_dir, 'test.png')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')
        
        result = processor.copy_local_image(test_image_path)
        
        assert result is not None
        assert os.path.exists(result)
        assert 'test.png' in result
    
    def test_copy_local_image_nonexistent(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test copying non-existent local image."""
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
        
        result = processor.copy_local_image('/nonexistent/image.png')
        assert result is None
    
    def test_process_images_markdown_syntax(self, mock_content_dir, mock_templates_dir, mock_output_dir, temp_dir):
        """Test processing images in markdown syntax."""
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
        
        # Create a test image
        test_image_path = os.path.join(temp_dir, 'test.png')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')
        
        # Test content with markdown image
        content = f"![Test Image]({test_image_path})"
        
        updated_content, images_converted = processor.process_images(content)
        
        assert '/images/' in updated_content
        assert '.webp' in updated_content
        assert images_converted >= 0
    
    def test_process_images_html_syntax(self, mock_content_dir, mock_templates_dir, mock_output_dir, temp_dir):
        """Test processing images in HTML syntax."""
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
        
        # Create a test image
        test_image_path = os.path.join(temp_dir, 'test.png')
        img = Image.new('RGB', (10, 10), color='red')
        img.save(test_image_path, 'PNG')
        
        # Test content with HTML image
        content = f'<img src="{test_image_path}" alt="Test">'
        
        updated_content, images_converted = processor.process_images(content)
        
        assert '/images/' in updated_content
        assert '.webp' in updated_content
        assert images_converted >= 0
    
    def test_process_images_invalid_extensions(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test processing content with non-image files."""
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
        
        # Test content with non-image file
        content = "![Document](document.pdf)"
        
        updated_content, images_converted = processor.process_images(content)
        
        # Content should remain unchanged
        assert updated_content == content
        assert images_converted == 0
