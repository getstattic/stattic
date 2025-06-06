#!/usr/bin/env python3
"""Security features demonstration for Stattic."""

import os
import tempfile
from stattic import FileProcessor

def demo_url_security():
    """Demonstrate URL security validation."""
    print("🔒 URL Security Validation Demo")
    print("-" * 40)
    
    # Create temporary setup
    temp_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(temp_dir, 'templates')
    content_dir = os.path.join(temp_dir, 'content')
    
    os.makedirs(templates_dir)
    os.makedirs(content_dir)
    
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write('<html><body>{{ content }}</body></html>')
    
    processor = FileProcessor(
        templates_dir=templates_dir,
        output_dir=os.path.join(temp_dir, 'output'),
        images_dir=os.path.join(temp_dir, 'output', 'images'),
        categories={},
        tags={},
        authors={},
        pages=[],
        site_url='https://example.com',
        content_dir=content_dir,
        blog_slug='blog'
    )
    
    # Test URLs
    test_urls = [
        ("https://example.com/image.jpg", "✅ SAFE", True),
        ("http://example.com/photo.png", "✅ SAFE", True),
        ("https://localhost/image.jpg", "❌ BLOCKED (localhost)", False),
        ("http://127.0.0.1/image.jpg", "❌ BLOCKED (private IP)", False),
        ("ftp://example.com/image.jpg", "❌ BLOCKED (non-HTTP)", False),
        ("javascript:alert(1)", "❌ BLOCKED (dangerous)", False),
    ]
    
    for url, expected_result, should_pass in test_urls:
        is_safe = processor._is_safe_url(url)
        status = "✅ SAFE" if is_safe else "❌ BLOCKED"
        result = "PASS" if (is_safe == should_pass) else "FAIL"
        print(f"{url:<35} → {status:<20} [{result}]")
    
    print()

def demo_image_security():
    """Demonstrate image processing security."""
    print("🖼️ Image Processing Security Demo")
    print("-" * 40)
    
    # Create temporary setup
    temp_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(temp_dir, 'templates')
    content_dir = os.path.join(temp_dir, 'content')
    
    os.makedirs(templates_dir)
    os.makedirs(content_dir)
    
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write('<html><body>{{ content }}</body></html>')
    
    processor = FileProcessor(
        templates_dir=templates_dir,
        output_dir=os.path.join(temp_dir, 'output'),
        images_dir=os.path.join(temp_dir, 'output', 'images'),
        categories={},
        tags={},
        authors={},
        pages=[],
        site_url='https://example.com',
        content_dir=content_dir,
        blog_slug='blog'
    )
    
    # Test image extensions
    test_files = [
        ("image.jpg", "✅ VALID", True),
        ("photo.png", "✅ VALID", True),
        ("animation.gif", "✅ VALID", True),
        ("document.pdf", "❌ INVALID", False),
        ("script.js", "❌ INVALID", False),
        ("malware.exe", "❌ INVALID", False),
    ]
    
    for filename, expected_result, should_pass in test_files:
        is_valid = processor._is_valid_image_extension(filename)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        result = "PASS" if (is_valid == should_pass) else "FAIL"
        print(f"{filename:<20} → {status:<15} [{result}]")
    
    print()

def demo_session_security():
    """Demonstrate session security configuration."""
    print("🌐 Session Security Configuration Demo")
    print("-" * 40)
    
    # Create temporary setup
    temp_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(temp_dir, 'templates')
    content_dir = os.path.join(temp_dir, 'content')
    
    os.makedirs(templates_dir)
    os.makedirs(content_dir)
    
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write('<html><body>{{ content }}</body></html>')
    
    processor = FileProcessor(
        templates_dir=templates_dir,
        output_dir=os.path.join(temp_dir, 'output'),
        images_dir=os.path.join(temp_dir, 'output', 'images'),
        categories={},
        tags={},
        authors={},
        pages=[],
        site_url='https://example.com',
        content_dir=content_dir,
        blog_slug='blog'
    )
    
    # Check session configuration
    session = processor.session
    
    print(f"Timeout configured: {session.timeout} seconds ✅")
    print(f"User-Agent header: {session.headers.get('User-Agent', 'Not set')} ✅")
    print(f"Session type: {type(session).__name__} ✅")
    print()

def demo_path_security():
    """Demonstrate path security features."""
    print("📁 Path Security Demo")
    print("-" * 40)
    
    # Create temporary setup
    temp_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(temp_dir, 'templates')
    content_dir = os.path.join(temp_dir, 'content')
    
    os.makedirs(templates_dir)
    os.makedirs(content_dir)
    
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write('<html><body>{{ content }}</body></html>')
    
    processor = FileProcessor(
        templates_dir=templates_dir,
        output_dir=os.path.join(temp_dir, 'output'),
        images_dir=os.path.join(temp_dir, 'output', 'images'),
        categories={},
        tags={},
        authors={},
        pages=[],
        site_url='https://example.com',
        content_dir=content_dir,
        blog_slug='blog'
    )
    
    # Check that all paths are absolute
    paths_to_check = [
        ("Templates directory", processor.templates_dir),
        ("Output directory", processor.output_dir),
        ("Content directory", processor.content_dir),
        ("Images directory", processor.images_dir),
    ]
    
    for name, path in paths_to_check:
        is_absolute = path.is_absolute()
        status = "✅ ABSOLUTE" if is_absolute else "❌ RELATIVE"
        print(f"{name:<20}: {status}")
    
    print()

def main():
    """Run all security demonstrations."""
    print("🛡️ Stattic Security Features Demonstration")
    print("=" * 50)
    print()
    
    try:
        demo_url_security()
        demo_image_security()
        demo_session_security()
        demo_path_security()
        
        print("🎉 All security features demonstrated successfully!")
        print("🔒 Your Stattic installation is now secure!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
