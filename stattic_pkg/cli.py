#!/usr/bin/env python3
"""
Command-line interface for Stattic - static site generator.
"""

import os
import sys
import argparse
import time
import shutil
import pkg_resources
from typing import List, Optional
from .core import Stattic
from .settings import StatticSettings

def create_starter_structure() -> None:
    """Create complete starter structure with templates, content, and assets."""
    current_dir = os.getcwd()
    
    # Create directory structure
    directories = [
        'templates',
        'content/posts',
        'content/pages', 
        'assets/css',
        'assets/js',
        'assets/images'
    ]
    
    for directory in directories:
        dir_path = os.path.join(current_dir, directory)
        if os.path.exists(dir_path):
            print(f"Directory already exists: {directory}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {directory}")
    
    # Copy template files from package
    try:
        template_source = pkg_resources.resource_filename('stattic_pkg', 'templates')
        template_dest = os.path.join(current_dir, 'templates')
        
        # Copy all template files
        for template_file in os.listdir(template_source):
            if template_file.endswith('.html'):
                src_path = os.path.join(template_source, template_file)
                dest_path = os.path.join(template_dest, template_file)
                
                if os.path.exists(dest_path):
                    print(f"Template already exists: templates/{template_file}")
                else:
                    shutil.copy2(src_path, dest_path)
                    print(f"Created template: templates/{template_file}")
    except Exception as e:
        print(f"Warning: Could not copy templates from package: {e}")
        print("You can copy templates manually from the Stattic repository.")
    
    # Copy asset files from package
    try:
        # Copy CSS assets
        css_source = pkg_resources.resource_filename('stattic_pkg', '../assets/css')
        css_dest = os.path.join(current_dir, 'assets', 'css')
        
        if os.path.exists(css_source):
            for asset_file in os.listdir(css_source):
                if asset_file.endswith(('.css', '.min.css')):
                    src_path = os.path.join(css_source, asset_file)
                    dest_path = os.path.join(css_dest, asset_file)
                    
                    if os.path.exists(dest_path):
                        print(f"CSS asset already exists: assets/css/{asset_file}")
                    else:
                        shutil.copy2(src_path, dest_path)
                        print(f"Created CSS asset: assets/css/{asset_file}")
        
        # Copy JS assets
        js_source = pkg_resources.resource_filename('stattic_pkg', '../assets/js')
        js_dest = os.path.join(current_dir, 'assets', 'js')
        
        if os.path.exists(js_source):
            for asset_file in os.listdir(js_source):
                if asset_file.endswith(('.js', '.min.js')):
                    src_path = os.path.join(js_source, asset_file)
                    dest_path = os.path.join(js_dest, asset_file)
                    
                    if os.path.exists(dest_path):
                        print(f"JS asset already exists: assets/js/{asset_file}")
                    else:
                        shutil.copy2(src_path, dest_path)
                        print(f"Created JS asset: assets/js/{asset_file}")
                        
    except Exception as e:
        print(f"Warning: Could not copy assets from package: {e}")
        print("You can copy assets manually from the Stattic repository.")
    
    # Create sample content files
    create_sample_content()
    
    # Create sample YAML files
    create_sample_yaml_files()
    
    print("\n✅ Starter structure created successfully!")
    print("\nNext steps:")
    print("1. Edit the configuration file (stattic.yml)")
    print("2. Customize templates in the 'templates/' directory")
    print("3. Add your content to 'content/posts/' and 'content/pages/'")
    print("4. Run 'stattic' to build your site")


def create_sample_content() -> None:
    """Create sample content files."""
    current_dir = os.getcwd()
    
    # Sample blog post
    sample_post = """---
title: "Welcome to Your New Static Site"
custom_url: welcome-to-your-new-static-site
author: 1
date: 2025-06-16
categories:
  - 1
tags:
  - 1
description: "This is your first blog post created with Stattic, a powerful static site generator."
keywords: "Stattic, static site generator, blog, getting started"
---

# Welcome to Your New Static Site!

Congratulations! You've successfully set up your new static site with **Stattic**. This is your first blog post, and it's designed to help you get started with creating amazing content.

## What is Stattic?

Stattic is a powerful, lightweight static site generator that converts your Markdown content into beautiful, fast-loading HTML websites. Here are some key features:

- **Fast and Secure**: Static sites load quickly and are inherently more secure
- **Easy to Use**: Write content in Markdown with simple YAML front matter
- **Flexible**: Customize templates with Jinja2 templating
- **SEO-Friendly**: Built-in support for meta tags, sitemaps, and RSS feeds
- **Image Optimization**: Automatic WebP conversion for better performance

## Getting Started

1. **Edit this post**: You can find this file at `content/posts/sample-post.md`
2. **Create new posts**: Add new `.md` files to the `content/posts/` directory
3. **Customize templates**: Modify the HTML templates in the `templates/` directory
4. **Configure settings**: Update your `stattic.yml` configuration file
5. **Build your site**: Run `stattic` to generate your static site

## Front Matter Options

Each post and page can include front matter with various options:

```yaml
---
title: "Your Post Title"
custom_url: your-custom-url
author: 1
date: 2025-06-16
categories:
  - 1
tags:
  - 1
description: "SEO description for this post"
keywords: "comma, separated, keywords"
featured_image: "path/to/image.jpg"
---
```

## What's Next?

- Explore the templates in the `templates/` directory
- Check out the sample page at `content/pages/sample-page.md`
- Read the documentation for more advanced features
- Start creating your own content!

Happy blogging with Stattic! 🚀
"""
    
    # Sample page
    sample_page = """---
title: "About This Site"
custom_url: about
author: 1
date: 2025-06-16
order: 1
description: "Learn more about this website and how it was built with Stattic."
keywords: "about, static site, Stattic"
---

# About This Site

Welcome to our website! This site was built using **Stattic**, a modern static site generator that makes it easy to create fast, secure, and beautiful websites.

## Our Mission

We believe in the power of simple, fast, and secure web technologies. Static sites offer numerous advantages:

- **Performance**: Lightning-fast loading times
- **Security**: No database vulnerabilities or server-side attacks
- **Reliability**: Simple hosting with excellent uptime
- **Cost-Effective**: Host anywhere, including free platforms like GitHub Pages

## Technology Stack

This site is powered by:

- **Stattic**: Static site generator
- **Markdown**: Content writing format
- **Jinja2**: Template engine
- **Tailwind CSS**: Utility-first CSS framework
- **WebP**: Optimized image format

## Get In Touch

Feel free to reach out to us through our [contact page](/contact/) or follow us on social media.

## About Stattic

Stattic is an open-source static site generator written in Python. It's designed to be simple, powerful, and secure. Key features include:

- Markdown content with YAML front matter
- Jinja2 templating system
- Automatic image optimization
- RSS feed and sitemap generation
- SEO-friendly output
- Easy deployment to any hosting platform

Learn more about Stattic at [stattic.site](https://stattic.site).
"""
    
    # Write sample files
    post_path = os.path.join(current_dir, 'content', 'posts', 'sample-post.md')
    if os.path.exists(post_path):
        print("Sample post already exists: content/posts/sample-post.md")
    else:
        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(sample_post)
        print("Created sample post: content/posts/sample-post.md")
    
    page_path = os.path.join(current_dir, 'content', 'pages', 'sample-page.md')
    if os.path.exists(page_path):
        print("Sample page already exists: content/pages/sample-page.md")
    else:
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(sample_page)
        print("Created sample page: content/pages/sample-page.md")


def create_sample_yaml_files() -> None:
    """Create sample YAML configuration files for authors, categories, and tags."""
    current_dir = os.getcwd()
    
    # Sample authors.yml
    authors_content = """# Authors configuration for Stattic
# Add your site authors here

1:
  name: "Site Author"
  email: "author@example.com"
  bio: "Welcome! I'm the author of this site."
  website: "https://example.com"
  twitter: "@username"
"""
    
    # Sample categories.yml
    categories_content = """# Categories configuration for Stattic
# Add your post categories here

1:
  name: "General"
  description: "General posts and updates"
  slug: "general"
"""
    
    # Sample tags.yml
    tags_content = """# Tags configuration for Stattic
# Add your post tags here

1:
  name: "Getting Started"
  description: "Posts about getting started with new topics"
  slug: "getting-started"
"""

    # Write YAML files
    authors_path = os.path.join(current_dir, 'content', 'authors.yml')
    if os.path.exists(authors_path):
        print("Authors file already exists: content/authors.yml")
    else:
        with open(authors_path, 'w', encoding='utf-8') as f:
            f.write(authors_content)
        print("Created sample authors: content/authors.yml")

    categories_path = os.path.join(current_dir, 'content', 'categories.yml')
    if os.path.exists(categories_path):
        print("Categories file already exists: content/categories.yml")
    else:
        with open(categories_path, 'w', encoding='utf-8') as f:
            f.write(categories_content)
        print("Created sample categories: content/categories.yml")

    tags_path = os.path.join(current_dir, 'content', 'tags.yml')
    if os.path.exists(tags_path):
        print("Tags file already exists: content/tags.yml")
    else:
        with open(tags_path, 'w', encoding='utf-8') as f:
            f.write(tags_content)
        print("Created sample tags: content/tags.yml")

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Stattic - Static Site Generator')
    parser.add_argument('--output', type=str,
                        help='Output directory for generated site')
    parser.add_argument('--content', type=str,
                        help='Content directory containing markdown files')
    parser.add_argument('--templates', type=str,
                        help='Templates directory')
    parser.add_argument('--assets', type=str,
                        help='Assets directory to copy to output')
    parser.add_argument('--posts-per-page', type=int,
                        help='Number of posts per page for pagination')
    parser.add_argument('--sort-by', type=str, choices=['date', 'title', 'author', 'order'], 
                        help='Sort posts by field')
    parser.add_argument('--fonts', type=str,
                        help='Comma-separated list of Google Fonts to include')
    parser.add_argument('--site-title', type=str, help='Site title for metadata')
    parser.add_argument('--site-tagline', type=str, help='Site tagline for metadata')
    parser.add_argument('--site-url', type=str,
                        help='Site URL for RSS feeds and sitemaps')
    parser.add_argument('--robots', type=str, choices=['public', 'private'], 
                        help='Robots.txt configuration')
    parser.add_argument('--llms', type=str, choices=['public', 'private'], 
                        help='LLMs.txt configuration for AI crawlers')
    parser.add_argument('--watch', action='store_true',
                        help='Watch for file changes and rebuild (not implemented)')
    parser.add_argument('--minify', action='store_true',
                        help='Minify CSS and JS assets')
    parser.add_argument('--blog-slug', type=str,
                        help="Custom slug for posts instead of 'blog'")
    parser.add_argument('--init', type=str, choices=['yml', 'yaml', 'json'], 
                        help='Create a sample configuration file')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    # Handle init command
    if args.init:
        settings_loader = StatticSettings()
        config_path = settings_loader.create_sample_config(args.init)
        print(f"Created sample configuration file: {config_path}")

        # Create complete starter structure
        print("\nCreating starter project structure...")
        create_starter_structure()

        print("\nYour new Stattic site is ready!")
        print("Edit the configuration file and templates, then run 'stattic' to build your site.")
        return

    # Load settings from configuration file
    settings_loader = StatticSettings()
    config_settings = settings_loader.load_settings()

    # Convert argparse Namespace to dict, excluding None values for proper merging
    args_dict = {k: v for k, v in vars(args).items() if v is not None}

    # Merge config file settings with command line arguments
    # Command line arguments take precedence
    final_settings = settings_loader.merge_with_args(args_dict)

    # Expand home directory if needed
    output_dir = os.path.expanduser(final_settings['output']) if final_settings['output'].startswith("~/") else final_settings['output']

    # Parse fonts
    fonts = final_settings['fonts']
    if isinstance(fonts, str):
        fonts = [font.strip() for font in fonts.split(',')]
    # Record start time
    overall_start_time = time.time()

    try:
        # Create Stattic instance
        generator = Stattic(
            content_dir=final_settings['content'],
            templates_dir=final_settings['templates'],
            output_dir=output_dir,
            posts_per_page=final_settings['posts_per_page'],
            sort_by=final_settings['sort_by'],
            fonts=fonts,
            site_url=final_settings['site_url'],
            assets_dir=final_settings['assets'],
            blog_slug=final_settings['blog_slug'],
            site_title=final_settings['site_title'],
            site_tagline=final_settings['site_tagline']
        )

        # Build the site
        generator.build()

        # Generate RSS and sitemap if site URL is provided
        if generator.site_url:
            generator.generate_rss_feed(generator.site_url, final_settings['site_title'])
            generator.generate_xml_sitemap(generator.site_url)
        else:
            generator.logger.info("Skipping RSS feed and XML sitemap (no site_url).")

        # Generate robots.txt and llms.txt
        generator.generate_robots_txt(final_settings['robots'])
        if final_settings['llms'] == 'public':
            generator.generate_llms_txt(final_settings['site_title'], final_settings['site_tagline'])

        # Show build statistics
        overall_end_time = time.time()
        total_time = overall_end_time - overall_start_time
        generator.logger.info(f"Site build completed in {total_time:.6f} seconds.")
        generator.logger.info(f"Total posts generated: {generator.posts_generated}")
        generator.logger.info(f"Total pages generated: {generator.pages_generated}")
        generator.logger.info(f"Total images converted to WebP: {generator.image_conversion_count}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()