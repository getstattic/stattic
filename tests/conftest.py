"""Test configuration and fixtures for Stattic tests."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
import yaml
from datetime import datetime

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_content_dir(temp_dir):
    """Create a mock content directory structure."""
    content_dir = Path(temp_dir) / 'content'
    posts_dir = content_dir / 'posts'
    pages_dir = content_dir / 'pages'
    
    # Create directories
    posts_dir.mkdir(parents=True)
    pages_dir.mkdir(parents=True)
    
    # Create sample files
    categories_file = content_dir / 'categories.yml'
    categories_file.write_text(yaml.dump({
        1: {'id': 1, 'name': 'General'},
        2: {'id': 2, 'name': 'Tech'}
    }))
    
    tags_file = content_dir / 'tags.yml'
    tags_file.write_text(yaml.dump({
        1: {'id': 1, 'name': 'python'},
        2: {'id': 2, 'name': 'web'}
    }))
    
    authors_file = content_dir / 'authors.yml'
    authors_file.write_text(yaml.dump({
        1: 'John Doe',
        2: 'Jane Smith'
    }))
    
    # Create sample post
    sample_post = posts_dir / 'test-post.md'
    sample_post.write_text("""---
title: Test Post
author: 1
date: 2023-01-01
categories: [1]
tags: [1, 2]
---

# Test Post

This is a test post with some content.

![Test Image](test-image.jpg)
""")
    
    # Create sample page
    sample_page = pages_dir / 'about.md'
    sample_page.write_text("""---
title: About
order: 1
---

# About Page

This is the about page.
""")
    
    return str(content_dir)

@pytest.fixture
def mock_templates_dir(temp_dir):
    """Create a mock templates directory."""
    templates_dir = Path(temp_dir) / 'templates'
    templates_dir.mkdir()
    
    # Create base template
    base_template = templates_dir / 'base.html'
    base_template.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>""")
    
    # Create post template
    post_template = templates_dir / 'post.html'
    post_template.write_text("""{% extends "base.html" %}
{% block content %}
<article>
    <h1>{{ title }}</h1>
    <div>{{ content|safe }}</div>
</article>
{% endblock %}""")
    
    # Create page template
    page_template = templates_dir / 'page.html'
    page_template.write_text("""{% extends "base.html" %}
{% block content %}
<div>
    <h1>{{ title }}</h1>
    <div>{{ content|safe }}</div>
</div>
{% endblock %}""")
    
    # Create index template
    index_template = templates_dir / 'index.html'
    index_template.write_text("""{% extends "base.html" %}
{% block content %}
<div>
    {% for post in posts %}
    <article>
        <h2>{{ post.title }}</h2>
        <div>{{ post.excerpt|safe }}</div>
    </article>
    {% endfor %}
</div>
{% endblock %}""")
    
    return str(templates_dir)

@pytest.fixture
def mock_output_dir(temp_dir):
    """Create a mock output directory."""
    output_dir = Path(temp_dir) / 'output'
    output_dir.mkdir()
    return str(output_dir)

@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    session = Mock()
    session.timeout = 30
    session.headers = {}
    return session

@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    # Create a minimal PNG image (1x1 pixel)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    return png_data

@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch('stattic.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_dt.min = datetime.min
        yield mock_dt
