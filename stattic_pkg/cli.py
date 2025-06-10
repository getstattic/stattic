#!/usr/bin/env python3
"""
Command-line interface for Stattic static site generator.
"""

import os
import sys
import argparse
import time
from .core import Stattic


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Stattic - Static Site Generator')
    parser.add_argument('--output', type=str, default='output',
                        help='Output directory for generated site')
    parser.add_argument('--content', type=str, default='content',
                        help='Content directory containing markdown files')
    parser.add_argument('--templates', type=str, default='templates',
                        help='Templates directory')
    parser.add_argument('--assets', type=str,
                        help='Assets directory to copy to output')
    parser.add_argument('--posts-per-page', type=int, default=5,
                        help='Number of posts per page for pagination')
    parser.add_argument('--sort-by', type=str, choices=['date', 'title', 'author', 'order'], 
                        default='date', help='Sort posts by field')
    parser.add_argument('--fonts', type=str,
                        help='Comma-separated list of Google Fonts to include')
    parser.add_argument('--site-title', type=str, help='Site title for metadata')
    parser.add_argument('--site-tagline', type=str, help='Site tagline for metadata')
    parser.add_argument('--site-url', type=str,
                        help='Site URL for RSS feeds and sitemaps')
    parser.add_argument('--robots', type=str, choices=['public', 'private'], 
                        default='public', help='Robots.txt configuration')
    parser.add_argument('--watch', action='store_true',
                        help='Watch for file changes and rebuild (not implemented)')
    parser.add_argument('--minify', action='store_true',
                        help='Minify CSS and JS assets (not implemented)')
    parser.add_argument('--blog-slug', type=str, default='blog',
                        help="Custom slug for posts instead of 'blog'")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()
    
    # Expand home directory if needed
    output_dir = os.path.expanduser(args.output) if args.output.startswith("~/") else args.output
    
    # Parse fonts
    fonts = [font.strip() for font in args.fonts.split(',')] if args.fonts else None

    # Record start time
    overall_start_time = time.time()

    try:
        # Create Stattic instance
        generator = Stattic(
            content_dir=args.content,
            templates_dir=args.templates,
            output_dir=output_dir,
            posts_per_page=args.posts_per_page,
            sort_by=args.sort_by,
            fonts=fonts,
            site_url=args.site_url,
            assets_dir=args.assets,
            blog_slug=args.blog_slug,
            site_title=args.site_title,
            site_tagline=args.site_tagline
        )

        # Build the site
        generator.build()

        # Generate RSS and sitemap if site URL is provided
        if generator.site_url:
            generator.generate_rss_feed(generator.site_url, args.site_title)
            generator.generate_xml_sitemap(generator.site_url)
        else:
            generator.logger.info("Skipping RSS feed and XML sitemap (no site_url).")

        # Generate robots.txt and llms.txt
        generator.generate_robots_txt(args.robots)
        generator.generate_llms_txt(args.site_title, args.site_tagline)

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
