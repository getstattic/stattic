"""
Stattic - A simple yet powerful static site generator.

Stattic takes content written in Markdown and uses Jinja2 templates to generate 
static HTML pages. It supports blog posts, tag and category pages, static pages,
custom URLs, SEO metadata, and more.
"""

__version__ = "1.0.0"
__author__ = "Robert DeVore"
__email__ = "me@robertdevore.com"

from .core import Stattic, FileProcessor

__all__ = ['Stattic', 'FileProcessor']
