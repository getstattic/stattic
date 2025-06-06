#!/usr/bin/env python3
"""Simple validation script to test Stattic fixes."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_imports():
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")
    try:
        from stattic import Stattic, FileProcessor, initializer
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_security_features():
    """Test security features."""
    print("🔒 Testing security features...")
    try:
        from stattic import FileProcessor
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        templates_dir = os.path.join(temp_dir, 'templates')
        content_dir = os.path.join(temp_dir, 'content')
        output_dir = os.path.join(temp_dir, 'output')
        
        os.makedirs(templates_dir)
        os.makedirs(content_dir)
        
        # Create basic template
        with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
            f.write('<html><body>{{ content }}</body></html>')
        
        processor = FileProcessor(
            templates_dir=templates_dir,
            output_dir=output_dir,
            images_dir=os.path.join(output_dir, 'images'),
            categories={},
            tags={},
            authors={},
            pages=[],
            site_url='https://example.com',
            content_dir=content_dir,
            blog_slug='blog'
        )
        
        # Test URL validation
        safe_urls = [
            'https://example.com/image.jpg',
            'http://example.com/image.png'
        ]
        
        unsafe_urls = [
            'https://localhost/image.jpg',
            'ftp://example.com/image.jpg',
            'javascript:alert(1)'
        ]
        
        for url in safe_urls:
            if not processor._is_safe_url(url):
                print(f"❌ Safe URL incorrectly blocked: {url}")
                return False
        
        for url in unsafe_urls:
            if processor._is_safe_url(url):
                print(f"❌ Unsafe URL incorrectly allowed: {url}")
                return False
        
        # Test session security
        if processor.session.timeout != 30:
            print("❌ Session timeout not configured")
            return False
        
        if 'User-Agent' not in processor.session.headers:
            print("❌ User-Agent header not set")
            return False
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("✅ Security features working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def test_type_hints():
    """Test that type hints are working."""
    print("📝 Testing type hints...")
    try:
        from stattic import FileProcessor
        import inspect
        
        # Check if type hints are present
        sig = inspect.signature(FileProcessor.__init__)
        
        # Check for type annotations
        has_annotations = any(
            param.annotation != inspect.Parameter.empty 
            for param in sig.parameters.values()
        )
        
        if not has_annotations:
            print("❌ Type hints not found")
            return False
        
        print("✅ Type hints working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Type hints test failed: {e}")
        return False

def test_error_handling():
    """Test improved error handling."""
    print("🛡️ Testing error handling...")
    try:
        from stattic import FileProcessor
        
        # Test with invalid directories
        try:
            FileProcessor(
                templates_dir='/nonexistent',
                output_dir='/tmp/test',
                images_dir='/tmp/test/images',
                categories={},
                tags={},
                authors={},
                pages=[],
                site_url=None,
                content_dir='/nonexistent',
                blog_slug='blog'
            )
            print("❌ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError:
            print("✅ Proper error handling for invalid directories")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_date_parsing():
    """Test improved date parsing."""
    print("📅 Testing date parsing...")
    try:
        from stattic import FileProcessor
        from datetime import datetime
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        templates_dir = os.path.join(temp_dir, 'templates')
        content_dir = os.path.join(temp_dir, 'content')
        
        os.makedirs(templates_dir)
        os.makedirs(content_dir)
        
        # Create basic template
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
            site_url=None,
            content_dir=content_dir,
            blog_slug='blog'
        )
        
        # Test various date formats
        test_dates = [
            ('2023-01-01', datetime(2023, 1, 1)),
            ('2023-01-01T12:00:00', datetime(2023, 1, 1, 12, 0, 0)),
            ('Jan 01, 2023', datetime(2023, 1, 1)),
            ('01/01/2023', datetime(2023, 1, 1)),
        ]
        
        for date_str, expected in test_dates:
            result = processor.parse_date(date_str)
            if result != expected:
                print(f"❌ Date parsing failed for {date_str}")
                return False
        
        # Test invalid date
        result = processor.parse_date('invalid-date')
        if result != datetime.min:
            print("❌ Invalid date not handled correctly")
            return False
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("✅ Date parsing working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Date parsing test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Stattic Fixes Validation")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_security_features,
        test_type_hints,
        test_error_handling,
        test_date_parsing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes validated successfully!")
        return 0
    else:
        print("💥 Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
