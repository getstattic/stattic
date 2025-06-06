"""Tests for main Stattic class."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stattic import Stattic


class TestStattic:
    """Test cases for Stattic class."""
    
    def test_init_valid_directories(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test Stattic initialization with valid directories."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            posts_per_page=5,
            sort_by='date',
            fonts=['Arial'],
            site_url='https://example.com',
            blog_slug='blog'
        )
        
        assert generator.content_dir.exists()
        assert generator.templates_dir.exists()
        assert generator.output_dir.exists()
        assert generator.posts_per_page == 5
        assert generator.sort_by == 'date'
        assert generator.fonts == ['Arial']
        assert generator.site_url == 'https://example.com'
        assert generator.blog_slug == 'blog'
    
    def test_init_invalid_templates_dir(self, mock_content_dir, mock_output_dir):
        """Test Stattic initialization with invalid templates directory."""
        with pytest.raises(FileNotFoundError, match="Templates directory"):
            Stattic(
                content_dir=mock_content_dir,
                templates_dir='/nonexistent',
                output_dir=mock_output_dir
            )
    
    def test_init_invalid_content_dir(self, mock_templates_dir, mock_output_dir):
        """Test Stattic initialization with invalid content directory."""
        with pytest.raises(FileNotFoundError, match="Content directory"):
            Stattic(
                content_dir='/nonexistent',
                templates_dir=mock_templates_dir,
                output_dir=mock_output_dir
            )
    
    def test_init_default_values(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test Stattic initialization with default values."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        assert generator.posts_per_page == 5
        assert generator.sort_by == 'date'
        assert generator.fonts == ['Quicksand']
        assert generator.site_url is None
        assert generator.blog_slug == 'blog'
    
    def test_posts_per_page_validation(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test posts_per_page validation ensures positive value."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            posts_per_page=0
        )
        
        assert generator.posts_per_page == 1  # Should be corrected to minimum of 1
    
    def test_site_url_normalization(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test site_url trailing slash removal."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            site_url='https://example.com/'
        )
        
        assert generator.site_url == 'https://example.com'
    
    def test_load_categories_and_tags(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test loading categories and tags from YAML files."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        # Categories and tags should be loaded from the mock files
        assert len(generator.categories) == 2
        assert generator.categories[1]['name'] == 'General'
        assert generator.categories[2]['name'] == 'Tech'
        
        assert len(generator.tags) == 2
        assert generator.tags[1]['name'] == 'python'
        assert generator.tags[2]['name'] == 'web'
    
    def test_load_authors(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test loading authors from YAML file."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        # Authors should be loaded from the mock file
        assert len(generator.authors) == 2
        assert generator.authors[1] == 'John Doe'
        assert generator.authors[2] == 'Jane Smith'
    
    def test_get_markdown_files(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test getting markdown files from directory."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        posts_dir = os.path.join(mock_content_dir, 'posts')
        markdown_files = generator.get_markdown_files(posts_dir)
        
        assert 'test-post.md' in markdown_files
        assert len(markdown_files) == 1
    
    def test_parse_date_methods(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test date parsing methods."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        # Test various date formats
        test_cases = [
            ('2023-01-01', datetime(2023, 1, 1)),
            ('2023-01-01T12:00:00', datetime(2023, 1, 1, 12, 0, 0)),
            ('Jan 01, 2023', datetime(2023, 1, 1)),
        ]
        
        for date_str, expected in test_cases:
            result = generator.parse_date(date_str)
            assert result == expected
    
    def test_create_output_dir(self, mock_content_dir, mock_templates_dir, temp_dir):
        """Test output directory creation."""
        output_dir = os.path.join(temp_dir, 'new_output')
        
        # Create a mock assets directory
        assets_dir = os.path.join(temp_dir, 'assets')
        os.makedirs(assets_dir)
        
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=output_dir,
            assets_dir=assets_dir
        )
        
        generator.create_output_dir()
        
        assert os.path.exists(output_dir)
    
    @patch('stattic.requests.Session.get')
    def test_download_fonts_success(self, mock_get, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test successful font download."""
        # Mock font CSS response
        mock_css_response = Mock()
        mock_css_response.status_code = 200
        mock_css_response.text = """
        @font-face {
            font-family: 'Test Font';
            src: url(https://fonts.gstatic.com/test.woff2) format('woff2');
        }
        """
        
        # Mock font file response
        mock_font_response = Mock()
        mock_font_response.status_code = 200
        mock_font_response.content = b'fake font data'
        
        mock_get.side_effect = [mock_css_response, mock_font_response]
        
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            fonts=['TestFont']
        )
        
        generator.download_fonts()
        
        # Check that font CSS file was created
        fonts_css_path = os.path.join(generator.assets_output_dir, 'css', 'fonts.css')
        assert os.path.exists(fonts_css_path)
    
    def test_minify_assets_missing_directories(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test minify_assets with missing CSS/JS directories."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        # This should not raise an exception even if directories don't exist
        generator.minify_assets()
    
    def test_render_template_not_found(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test template rendering with non-existent template."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        result = generator.render_template('nonexistent.html', title='Test')
        assert 'Error: The template' in result
    
    def test_render_template_success(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test successful template rendering."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir,
            site_url='https://example.com'
        )
        
        result = generator.render_template('base.html', title='Test Title')
        assert 'Test Title' in result
        assert '<html>' in result
    
    def test_session_configuration(self, mock_content_dir, mock_templates_dir, mock_output_dir):
        """Test that session is properly configured with security settings."""
        generator = Stattic(
            content_dir=mock_content_dir,
            templates_dir=mock_templates_dir,
            output_dir=mock_output_dir
        )
        
        assert generator.session.timeout == 30
        assert 'User-Agent' in generator.session.headers
        assert generator.session.headers['User-Agent'] == 'Stattic/1.0'
