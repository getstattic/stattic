import os
import shutil
import markdown
import yaml
import argparse
import logging
import time
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
import re
import requests
from PIL import Image
import csscompressor
import rjsmin
import mistune
from xml.sax.saxutils import escape
from urllib.parse import urlparse
from email.utils import formatdate
from hashlib import md5
import xml.etree.ElementTree as ET

GOOGLE_FONTS_API = 'https://fonts.googleapis.com/css2?family={font_name}:wght@{weights}&display=swap'

class Stattic:
    def __init__(self, content_dir='content', templates_dir='templates', output_dir='output', posts_per_page=5, sort_by='date', fonts=None, site_url=None, assets_dir=None):
        self.content_dir = content_dir
        self.posts_dir = os.path.join(content_dir, 'posts')
        self.pages_dir = os.path.join(content_dir, 'pages')
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.logger = self.setup_logging()
        self.images_dir = os.path.join(output_dir, 'images')  # Images directory for downloads
        self.assets_src_dir = assets_dir or os.path.join(os.path.dirname(__file__), 'assets')  # Custom or default assets folder
        self.assets_output_dir = os.path.join(output_dir, 'assets')  # Output folder for assets
        self.fonts = fonts if fonts else ['Quicksand']  # Default to Quicksand if no font is passed
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.posts = []  # Store metadata of all posts for index, archive, and RSS generation
        self.pages = []  # Track pages for navigation
        self.pages_generated = 0
        self.posts_generated = 0
        self.posts_per_page = posts_per_page
        self.sort_by = sort_by
        self.categories = {}
        self.tags = {}
        self.authors = {}  # Store author mappings
        self.image_conversion_count = 0  # Track total number of converted images
        self.site_url = site_url.rstrip('/') if site_url else None  # Ensure no trailing slash
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')  # Store the log file path

        # Validate templates directory
        if not os.path.isdir(self.templates_dir):
            raise FileNotFoundError(f"Templates directory '{self.templates_dir}' does not exist.")

        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

        # Log resolved paths
        self.logger.info(f"Using templates directory: {self.templates_dir}")

        # Load categories, tags, and authors from YAML files
        self.load_categories_and_tags()
        self.load_authors()

        # Ensure images directory exists
        os.makedirs(self.images_dir, exist_ok=True)

        # Ensure pages are loaded before generating posts or pages
        self.load_pages()

        # Add custom markdown filter
        self.env.filters['markdown'] = self.markdown_filter

    def markdown_filter(self, text):
        """Convert markdown text to HTML using Mistune 2.x with preserved line breaks in code blocks."""
        start_time = time.time()

        # Custom renderer to preserve line breaks in code blocks
        class CustomRenderer(mistune.HTMLRenderer):
            def block_code(self, code, info=None):
                # Ensure line breaks and spacing are preserved within <pre><code>
                escaped_code = mistune.escape(code)
                return '<pre style="white-space: pre-wrap;"><code>{}</code></pre>'.format(escaped_code)

        # Initialize Mistune with custom renderer and necessary plugins
        markdown_parser = mistune.create_markdown(
            renderer=CustomRenderer(),
            plugins=['table', 'task_lists', 'strikethrough']
        )

        # Convert Markdown content to HTML
        html_output = markdown_parser(text)

        end_time = time.time()
        # Log the HTML output for debugging purposes
        self.logger.info(f"Converted Markdown to HTML using Mistune (Time taken: {end_time - start_time:.6f} seconds)")

        return html_output

    def setup_logging(self):
        """Setup the logger to write both to a file and the console."""
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        log_file = os.path.join(logs_dir, f"stattic_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

        logger = logging.getLogger('stattic')
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        logger.info(f"Logging initialized. Logs stored at {log_file}")

        return logger

    def minify_assets(self):
        """Minify all CSS and JS files into single files."""
        try:
            # Paths to CSS and JS files
            css_dir = os.path.join(self.assets_output_dir, 'css')
            js_dir = os.path.join(self.assets_output_dir, 'js')

            # Output paths for minified files
            minified_css_path = os.path.join(css_dir, 'stattic.min.css')
            minified_js_path = os.path.join(js_dir, 'stattic.min.js')

            # Minify CSS files
            all_css_content = ""
            for file in os.listdir(css_dir):
                if file.endswith(".css") and not file.endswith(".min.css"):
                    with open(os.path.join(css_dir, file), 'r') as f:
                        all_css_content += f.read()
            minified_css_content = csscompressor.compress(all_css_content)
            with open(minified_css_path, 'w') as f:
                f.write(minified_css_content)
            self.logger.info(f"Minified CSS into {minified_css_path}")

            # Minify JS files
            all_js_content = ""
            for file in os.listdir(js_dir):
                if file.endswith(".js") and not file.endswith(".min.js"):
                    with open(os.path.join(js_dir, file), 'r') as f:
                        all_js_content += f.read()
            minified_js_content = rjsmin.jsmin(all_js_content)
            with open(minified_js_path, 'w') as f:
                f.write(minified_js_content)
            self.logger.info(f"Minified JS into {minified_js_path}")

        except Exception as e:
            self.logger.error(f"Failed to minify assets: {e}")

    def format_date(self, date_str=None):
        """Format the date from 'YYYY-MM-DDTHH:MM:SS' to 'Month DD, YYYY'."""
        if not date_str:
            return ''  # Return an empty string if no date is provided

        # Check if date_str is already a datetime object
        if isinstance(date_str, datetime):
            date_obj = date_str
        elif isinstance(date_str, date):
            # If it's a datetime.date object, convert it to datetime
            date_obj = datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, str):
            # Attempt to parse and format the date with time
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                try:
                    # Fallback to parsing date without time
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    # If parsing fails, return the original date string
                    return date_str
        else:
            # If it's an unexpected type, return an empty string or handle accordingly
            return ''

        # Return the formatted date
        return date_obj.strftime('%b %d, %Y')

    def load_categories_and_tags(self):
        """Load categories and tags from YAML files."""
        try:
            with open(os.path.join(self.content_dir, 'categories.yml'), 'r') as cat_file:
                self.categories = yaml.safe_load(cat_file) or {}
            with open(os.path.join(self.content_dir, 'tags.yml'), 'r') as tag_file:
                self.tags = yaml.safe_load(tag_file) or {}
            self.logger.info(f"Loaded {len(self.categories)} categories and {len(self.tags)} tags")
        except FileNotFoundError as e:
            self.logger.error(f"YAML file not found: {e}")
        except Exception as e:
            self.logger.error(f"Error loading categories/tags: {e}")

    def load_authors(self):
        """Load authors from a YAML file."""
        try:
            with open(os.path.join(self.content_dir, 'authors.yml'), 'r') as authors_file:
                self.authors = yaml.safe_load(authors_file) or {}
            self.logger.info(f"Loaded {len(self.authors)} authors")
        except FileNotFoundError as e:
            self.logger.error(f"Authors YAML file not found: {e}")
        except Exception as e:
            self.logger.error(f"Error loading authors: {e}")

    def get_author_name(self, author_id):
        """Fetch the author's name based on the author_id."""
        return self.authors.get(author_id, "Unknown")

    def load_pages(self):
        """Load pages for the navigation and use across all templates."""
        try:
            page_files = self.get_markdown_files(self.pages_dir)
            for page_file in page_files:
                filepath = os.path.join(self.pages_dir, page_file)
                metadata, _ = self.parse_markdown_with_metadata(filepath)

                title = metadata.get('title', 'Untitled')
                if isinstance(title, dict):
                    title = title.get('rendered', 'Untitled')

                order = metadata.get('order', 100)
                
                # Convert nav_hide to lowercase and treat as a string
                nav_hide = str(metadata.get('nav_hide', '')).strip().lower()

                # Add page metadata to self.pages
                self.pages.append({
                    'title': title,
                    'permalink': f"{metadata.get('custom_url', page_file.replace('.md', ''))}/",  # Added trailing slash
                    'order': order,
                    'nav_text': metadata.get('nav_text'),
                    'nav_hide': nav_hide
                })

            # Sort pages by order
            self.pages = sorted(self.pages, key=lambda x: x['order'])
            self.logger.info(f"Loaded {len(self.pages)} pages for navigation")

        except Exception as e:
            self.logger.error(f"Failed to load pages: {e}")

    def download_image(self, url, output_dir, markdown_file_path=None):
        """Download an image and save it locally, or check if it's a local image."""
        try:
            # Only process URLs with common image file extensions
            if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')):
                #self.logger.warning(f"Skipping non-image URL: {url}")
                return None

            # Check if the URL is relative (starts with a slash or '..' indicating local reference)
            if url.startswith('/') or url.startswith('../') or not url.startswith('http'):
                # If markdown_file_path is provided, resolve the local path relative to it
                if markdown_file_path:
                    # Resolve the relative path based on the markdown file's directory
                    markdown_dir = os.path.dirname(markdown_file_path)
                    local_image_path = os.path.abspath(os.path.join(markdown_dir, url))
                else:
                    # Otherwise, resolve it relative to the content directory
                    local_image_path = os.path.abspath(os.path.join(self.content_dir, url))

                if os.path.exists(local_image_path):
                    self.logger.info(f"Found local image: {local_image_path}")
                    return local_image_path
                else:
                    self.logger.error(f"Local image not found: {local_image_path}")
                    return None

            # If it's not a local path, treat it as an external URL
            response = requests.get(url)
            response.raise_for_status()  # Ensure the request was successful

            # Extract the image file name
            image_name = os.path.basename(url)
            image_path = os.path.join(output_dir, image_name)

            # Save the image
            with open(image_path, 'wb') as image_file:
                image_file.write(response.content)

            self.logger.info(f"Downloaded image: {url}")
            return image_path
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download image {url}: {e}")
            return None

    def download_fonts(self):
        """Download Google Fonts based on provided names and save the font files locally, dynamically set font-family in CSS."""
        try:
            # Default to Quicksand if no fonts are provided
            if not self.fonts:
                self.fonts = ['Quicksand']

            # CSS content to store the @font-face rules and custom class names
            css_content = ""
            font_family_names = []

            # Create the fonts and CSS directories if they don't exist
            fonts_output_path = os.path.join(self.assets_output_dir, 'fonts')
            fonts_css_path = os.path.join(self.assets_output_dir, 'css', 'fonts.css')
            os.makedirs(fonts_output_path, exist_ok=True)
            os.makedirs(os.path.dirname(fonts_css_path), exist_ok=True)

            # List of font weights to download
            font_weights = [300, 400, 500, 600, 700]

            for font in self.fonts:
                font_cleaned = font.strip().replace(' ', '+')  # Replace spaces with +
                font_family_names.append(font.strip())  # Store the clean name for font-family usage

                # Explicitly request each weight to ensure all are downloaded
                for weight in font_weights:
                    google_font_url = GOOGLE_FONTS_API.format(font_name=font_cleaned, weights=weight)
                    font_file_name_woff2 = f"{font.strip().lower()}-{weight}.woff2"  # woff2 format
                    font_file_name_ttf = f"{font.strip().lower()}-{weight}.ttf"  # ttf format
                    font_output_file_woff2 = os.path.join(fonts_output_path, font_file_name_woff2)
                    font_output_file_ttf = os.path.join(fonts_output_path, font_file_name_ttf)

                    # Check if the font file already exists for woff2 format
                    if os.path.exists(font_output_file_woff2) and os.path.getsize(font_output_file_woff2) > 0:
                        self.logger.info(f"Font {font} ({weight}) already exists in woff2. Skipping download.")
                    else:
                        # Download the CSS from Google Fonts for each weight
                        response = requests.get(google_font_url)
                        if response.status_code == 200:
                            css_data = response.text

                            # Extract URLs and font formats from the CSS data
                            font_urls = re.findall(r'url\((.*?)\) format\((.*?)\);', css_data)

                            for font_url, format_type in font_urls:
                                # Download the actual font file
                                font_file_response = requests.get(font_url)
                                if font_file_response.status_code == 200:
                                    # Save woff2 if it's available
                                    with open(font_output_file_woff2, 'wb') as f:
                                        f.write(font_file_response.content)
                                    self.logger.info(f"Downloaded {font} ({weight}) in woff2 from {font_url}")

                                else:
                                    self.logger.error(f"Failed to download font file from {font_url}")
                        else:
                            self.logger.error(f"Failed to fetch font CSS from Google Fonts for {font} weight {weight}")

                    # Generate @font-face rule with multiple formats (woff2, ttf)
                    css_content += f"""
@font-face {{
    font-family: '{font.strip()}';
    font-style: normal;
    font-weight: {weight};
    font-display: swap;
    src: url('../fonts/{font_file_name_woff2}') format('woff2'), 
         url('../fonts/{font_file_name_ttf}') format('truetype');
}}
"""

                # Apply the font-family globally (optional customization)
                css_content += f"""
body {{
    font-family: '{font.strip()}', sans-serif;
}}
"""

            # Write the @font-face rules to the fonts.css file
            with open(fonts_css_path, 'w') as f:
                f.write(css_content)

            self.logger.info(f"Downloaded fonts and generated CSS: {', '.join(self.fonts)}")
        except Exception as e:
            self.logger.error(f"Failed to download fonts: {e}")

    def copy_assets_to_output(self):
        """Copy the local or user-specified assets folder (CSS, JS, etc.) to the output directory."""
        try:
            if os.path.exists(self.assets_src_dir):
                # Copy the specified or default assets directory to the output directory
                shutil.copytree(self.assets_src_dir, self.assets_output_dir, dirs_exist_ok=True)
                self.logger.info(f"Copied assets from {self.assets_src_dir} to {self.assets_output_dir}")
            else:
                self.logger.error(f"Assets directory not found: {self.assets_src_dir}")
        except Exception as e:
            self.logger.error(f"Failed to copy assets: {e}")
            raise

    def create_output_dir(self):
        """Create the output directory if it doesn't exist, and copy assets."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Created output directory: {self.output_dir}")

        # Ensure that the assets are copied to the output directory
        self.copy_assets_to_output()

    def convert_image_to_webp(self, image_path):
        """Convert an image to WebP format and delete the original."""
        try:
            img = Image.open(image_path)
            webp_path = image_path.rsplit('.', 1)[0] + '.webp'
            img.save(webp_path, 'WEBP')
            self.logger.info(f"Converted image to WebP: {webp_path}")
            
            # Remove the original image file to save space
            os.remove(image_path)
            self.logger.info(f"Removed original image: {image_path}")
            
            self.image_conversion_count += 1  # Increment conversion count
            return webp_path
        except Exception as e:
            self.logger.error(f"Failed to convert {image_path} to WebP: {e}")
            return None

    def process_images(self, content):
        """Find all image URLs in the content, download, convert them, and replace with local WebP paths."""
        # Extract image URLs from Markdown syntax
        markdown_image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)
        
        # Extract image URLs from HTML <img> tags, including src, srcset, and wrapped links
        html_image_urls = re.findall(r'<img\s+[^>]*src="([^"]+)"', content)
        href_urls = re.findall(r'<a\s+[^>]*href="([^"]+)"', content)
        
        # Extract srcset image URLs, multiple URLs per srcset
        srcset_urls = re.findall(r'srcset="([^"]+)"', content)
        all_srcset_urls = []
        for srcset in srcset_urls:
            all_srcset_urls.extend([url.strip().split(' ')[0] for url in srcset.split(',')])
        
        # Combine all unique image URLs
        image_urls = set(markdown_image_urls + html_image_urls + href_urls + all_srcset_urls)
        
        local_image_paths = {}
        
        # Process all unique image URLs found
        for url in image_urls:
            # Ensure the URL points to an image file
            if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')):
                #self.logger.warning(f"Skipping non-image URL: {url}")
                continue

            self.logger.info(f"Processing image: {url}")
            image_name = os.path.basename(url)
            webp_image_path = os.path.join(self.images_dir, image_name.rsplit('.', 1)[0] + '.webp')

            # Check if the WebP version already exists
            if os.path.exists(webp_image_path):
                self.logger.info(f"Using existing WebP image: {webp_image_path}")
                local_image_paths[url] = f"images/{os.path.basename(webp_image_path)}"
            else:
                # Download and convert the image if the WebP version does not exist
                image_path = self.download_image(url, self.images_dir)
                if image_path:
                    webp_path = self.convert_image_to_webp(image_path)
                    if webp_path:
                        local_image_paths[url] = f"images/{os.path.basename(webp_path)}"

        # Replace `href` and `src` attributes directly
        for url, webp_path in local_image_paths.items():
            content = content.replace(f'href="{url}"', f'href="{webp_path}"')
            content = content.replace(f'src="{url}"', f'src="{webp_path}"')

        # Replace `srcset` attributes with all processed image URLs
        def replace_srcset(match):
            srcset_value = match.group(1)
            srcset_entries = srcset_value.split(',')

            # Prepare to replace each URL in the srcset
            new_srcset_entries = []
            for entry in srcset_entries:
                parts = entry.strip().split(' ')
                url_part = parts[0]
                # Check if the URL was processed and exists in local_image_paths
                if url_part in local_image_paths:
                    parts[0] = local_image_paths[url_part]
                new_srcset_entries.append(' '.join(parts))

            # Reconstruct the srcset attribute with all updated URLs
            return 'srcset="' + ', '.join(new_srcset_entries) + '"'

        # Use regex to find srcset attributes and replace them using the function
        content = re.sub(r'srcset="([^"]+)"', replace_srcset, content)

        return content

    def parse_date(self, date_str):
        """Parse the date string into a datetime object."""
        if isinstance(date_str, datetime):
            return date_str
        elif isinstance(date_str, date):
            return datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, str):
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%b %d, %Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        self.logger.warning(f"Unable to parse date: {date_str}. Using minimum date as fallback.")
        return datetime.min  # Fallback to the earliest date for sorting

    def parse_markdown_with_metadata(self, filepath):
        """Extract frontmatter and markdown content from the file, process images."""
        try:
            start_time = time.time()
            with open(filepath, 'r') as f:
                content = f.read()

            # Check if the content contains frontmatter (starts with ---)
            if content.startswith('---'):
                parts = content.split('---', 2)  # Splitting into 3 parts: '', frontmatter, content
                if len(parts) == 3:
                    frontmatter, markdown_content = parts[1], parts[2]
                    metadata = yaml.safe_load(frontmatter) or {}
                else:
                    self.logger.warning(f"Malformed frontmatter in {filepath}. Treating entire content as markdown.")
                    metadata, markdown_content = {}, content
            else:
                self.logger.info(f"No frontmatter in {filepath}. Treating as pure markdown.")
                metadata, markdown_content = {}, content

            # Parse and normalize the date in metadata
            if 'date' in metadata:
                metadata['date'] = self.parse_date(metadata['date'])

            # Process images in the markdown content
            markdown_content = self.process_images(markdown_content)

            duration = time.time() - start_time
            self.logger.info(f"Parsed markdown file: {filepath} (Time taken: {duration:.6f} seconds)")
            return metadata, markdown_content
        except Exception as e:
            self.logger.error(f"Failed to parse markdown file: {filepath} - {e}")
            raise

    def get_markdown_files(self, directory):
        """Retrieve a list of Markdown files in a given directory."""
        try:
            start_time = time.time()
            files = [f for f in os.listdir(directory) if f.endswith('.md')]
            duration = time.time() - start_time
            self.logger.info(f"Found {len(files)} markdown files in {directory} (Time taken: {duration:.6f} seconds)")
            return files
        except FileNotFoundError as e:
            self.logger.error(f"Directory not found: {directory}")
            raise

    def calculate_relative_path(self, current_output_dir):
        """Calculate the relative path from the current_output_dir to the root output directory."""
        # Get the absolute paths
        root = os.path.abspath(self.output_dir)
        current = os.path.abspath(current_output_dir)

        # Get the relative path
        relative = os.path.relpath(root, current)

        # If relative is '.', it means current_output_dir is root
        return './' if relative == '.' else relative + '/'

    def build_post_or_page(self, metadata, html_content, post_slug, output_dir, is_page=False):
        """Render the post or page template and write it to the output directory."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join(output_dir, 'index.html')

            # Fix title rendering to ensure it is a string, not a dict
            title = metadata.get('title', 'Untitled')
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')

            # Get author name using the helper function
            author_name = self.get_author_name(metadata.get('author', 'Unknown'))

            # Format the date using the format_date helper function
            formatted_date = self.format_date(metadata.get('date'))

            post_categories = []
            for cat_id in metadata.get('categories', []):
                if isinstance(cat_id, int):
                    category = self.categories.get(cat_id, {})
                    if isinstance(category, dict):
                        post_categories.append(category.get('name', f"Unknown (ID: {cat_id})"))
                    elif isinstance(category, str):
                        post_categories.append(category)  # Use the string directly
                    else:
                        self.logger.error(f"Invalid category format for ID: {cat_id}")
                else:
                    self.logger.error(f"Invalid category ID: {cat_id}")

            post_tags = []
            for tag_id in metadata.get('tags', []):
                if isinstance(tag_id, int):
                    tag = self.tags.get(tag_id, {})
                    post_tags.append(tag.get('name', f"Unknown (ID: {tag_id})"))
                else:
                    self.logger.error(f"Invalid tag ID: {tag_id}")

            # Calculate relative_path based on directory depth
            relative_path = self.calculate_relative_path(output_dir)

            # Get the template part from the frontmatter or fallback to 'post.html' or 'page.html'
            template_part = metadata.get('template', None)

            # If no template is specified, fallback to post.html or page.html
            if template_part:
                template_name = f"post-{template_part}.html" if not is_page else f"page-{template_part}.html"
            else:
                template_name = 'page.html' if is_page else 'post.html'

            rendered_html = self.render_template(
                template_name,
                content=html_content,
                title=title,
                author=author_name,
                date=formatted_date,
                categories=post_categories,
                tags=post_tags,
                featured_image=metadata.get('featured_image', None),
                seo_title=metadata.get('seo_title', title),
                seo_keywords=metadata.get('keywords', ''),
                seo_description=metadata.get('description', ''),
                lang=metadata.get('lang', 'en'),
                pages=self.pages,  # Pass pages for consistent navigation
                page=metadata,  # Pass metadata as 'page' for template
                metadata=metadata,
                relative_path=relative_path  # Pass relative_path to templates
            )

            # Write the rendered HTML to the output file
            with open(output_file_path, 'w') as output_file:
                output_file.write(rendered_html)

            self.logger.info(f"Generated {'page' if is_page else 'post'}: {output_file_path}")
            if is_page:
                self.pages_generated += 1
            else:
                self.posts_generated += 1

        except Exception as e:
            self.logger.error(f"Failed to generate {'page' if is_page else 'post'} {post_slug}: {e}")
            raise

    def render_template(self, template_name, **context):
        """Render a template using Jinja2 with the provided context."""
        try:
            start_time = time.time()
            template = self.env.get_template(template_name)
            context['minify'] = getattr(args, 'minify', False)  # Pass the minify flag
            rendered_template = template.render(context)
            duration = time.time() - start_time
            self.logger.info(f"Rendered template: {template_name} (Time taken: {duration:.6f} seconds)")
            return rendered_template
        except TemplateNotFound as e:
            self.logger.error(f"Template not found: {template_name}")
            return f"Error: The template {e} could not be found."
        except TemplateSyntaxError as e:
            self.logger.error(f"Template syntax error in {e.filename} at line {e.lineno}: {e.message}")
            return f"Error: Template syntax error in {e.filename} at line {e.lineno}: {e.message}"

    def build_posts_and_pages(self):
        """Process and build all posts and pages."""
        # Process posts
        post_files = self.get_markdown_files(self.posts_dir)
        for post_file in post_files:
            filepath = os.path.join(self.posts_dir, post_file)

            # Extract metadata and markdown content
            metadata, md_content = self.parse_markdown_with_metadata(filepath)

            # Skip drafts
            if metadata.get('draft', False):
                self.logger.info(f"Skipping draft: {post_file}")
                continue

            # Convert markdown content to HTML
            html_content = self.convert_markdown_to_html(md_content)

            # Determine the output directory for the post
            post_slug = metadata.get('custom_url', post_file.replace('.md', ''))
            post_output_dir = os.path.join(self.output_dir, 'blog', post_slug)

            # Render the post and write it to the output directory
            self.build_post_or_page(metadata, html_content, post_slug, post_output_dir, is_page=False)

            # Determine the permalink (relative path)
            permalink = f"blog/{post_slug}/"

            # Collect post metadata for the index page
            # When collecting post metadata
            post_metadata = {
                'title': metadata.get('title', 'Untitled'),
                'excerpt': self.markdown_filter(metadata.get('excerpt', self.generate_excerpt(md_content))),
                'permalink': f"blog/{post_slug}/",
                'date': self.format_date(metadata.get('date')),
                'metadata': metadata
            }
            self.posts.append(post_metadata)
            
            self.logger.info(f"Collected {len(self.posts)} posts for the index page.")

        # Process pages (save in root directory)
        page_files = self.get_markdown_files(self.pages_dir)
        for page_file in page_files:
            filepath = os.path.join(self.pages_dir, page_file)

            # Extract metadata and markdown content
            metadata, md_content = self.parse_markdown_with_metadata(filepath)

            # Convert markdown content to HTML
            html_content = self.convert_markdown_to_html(md_content)

            # Determine the output directory for the page (save directly in the root output folder)
            page_slug = metadata.get('custom_url', page_file.replace('.md', ''))
            page_output_dir = os.path.join(self.output_dir, page_slug)  # No 'pages' subfolder

            # Render the page and write it to the output directory
            self.build_post_or_page(metadata, html_content, page_slug, page_output_dir, is_page=True)

    def convert_markdown_to_html(self, markdown_content):
        """Convert Markdown content to HTML."""
        # Use the custom markdown filter for consistent processing
        return self.markdown_filter(markdown_content)

    def generate_excerpt(self, content):
        """Generate an excerpt from the post content if no excerpt is provided."""
        if not content:
            return ''
        words = content.split()[:30]  # Take the first 30 words
        return ' '.join(words) + '...'

    def build_index_page(self):
        """Render and build the index (homepage) with the list of posts."""
        try:
            # Ensure all posts have a valid parsed date for sorting
            for post in self.posts:
                post_date_str = post.get('date', '')
                post['parsed_date'] = self.parse_date(post_date_str)  # Add parsed_date for sorting

            # Sort posts by parsed_date in descending order
            posts_for_index = sorted(
                self.posts,
                key=lambda post: post.get('parsed_date', datetime.min),  # Fallback to the earliest date
                reverse=True
            )[:self.posts_per_page]

            # Render the index template
            rendered_html = self.render_template(
                'index.html',
                posts=posts_for_index,
                pages=self.pages,
                page={}  # Provide an empty page context
            )

            # Save the rendered HTML to the output directory
            output_file_path = os.path.join(self.output_dir, 'index.html')
            with open(output_file_path, 'w') as output_file:
                output_file.write(rendered_html)

            self.logger.info(f"Generated index page at {output_file_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate index page: {e}")

    def build_static_pages(self):
        """Generate static pages like contact page."""
        # Example for a static contact page
        output_dir = os.path.join(self.output_dir, 'contact')
        os.makedirs(output_dir, exist_ok=True)
        rendered_html = self.render_template('page.html', title="Contact Us", content="<p>Contact page content</p>", relative_path='../')
        with open(os.path.join(output_dir, 'index.html'), 'w') as output_file:
            output_file.write(rendered_html)
        self.logger.info(f"Generated contact page: {output_dir}")

    def generate_rss_feed(self, site_url, site_name=None):
        """Generate an RSS feed from the list of posts."""
        try:
            # Ensure the site_url ends with a '/'
            if not site_url.endswith('/'):
                site_url += '/'

            # Extract site name dynamically from the site_url domain if not provided
            if not site_name:
                parsed_url = urlparse(site_url)
                site_name = parsed_url.netloc.replace('www.', '')  # Remove 'www.' if present

            # Fix: Avoid adding 'https://' twice, use site_url directly for the feed URL
            feed_url = f"{site_url.rstrip('/')}/feed/index.xml"

            # RSS header information with proper escaping
            rss_feed = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>{site_name}</title>
<link>{site_url}</link>
<description>{site_description}</description>
<atom:link href="{feed_url}" rel="self" type="application/rss+xml" />
<lastBuildDate>{build_date}</lastBuildDate>
<language>en-us</language>
"""

            # Site description using site_name
            site_description = f"Latest posts from {escape(site_name)}"
            build_date = formatdate(timeval=None, localtime=False, usegmt=True)  # RFC-822 format

            # Format the RSS header with the site information
            rss_feed = rss_feed.format(
                site_name=escape(site_name),
                site_url=escape(site_url),
                site_description=site_description,
                feed_url=escape(feed_url),
                build_date=build_date
            )

            # Add each post to the RSS feed
            for post in self.posts:
                post_title = escape(post.get('title', 'Untitled'))  # Escape special characters
                post_permalink = f"{site_url.rstrip('/')}/{post.get('permalink', '')}"  # Absolute URL

                # Strip the <p> tags from the excerpt and ensure plain text, escape it
                post_description = escape(re.sub(r'<.*?>', '', post.get('excerpt', 'No description available')))

                # Handle different formats for post date
                post_date_str = post.get('date')
                try:
                    if isinstance(post_date_str, datetime):
                        post_pubdate = post_date_str.strftime('%a, %d %b %Y %H:%M:%S +0000')
                    elif isinstance(post_date_str, str):
                        post_pubdate_dt = datetime.strptime(post_date_str, '%Y-%m-%dT%H:%M:%S')
                        post_pubdate = post_pubdate_dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
                    else:
                        # Fallback to the current date if parsing fails
                        post_pubdate = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                except ValueError:
                    # Attempt to parse date without time
                    try:
                        post_pubdate_dt = datetime.strptime(post_date_str, '%Y-%m-%d')
                        post_pubdate = post_pubdate_dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
                    except (ValueError, TypeError):
                        post_pubdate = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

                # Generate a unique guid for each post (could be permalink-based hash)
                guid = md5(post_permalink.encode('utf-8')).hexdigest()

                rss_feed += f"""
<item>
<title>{post_title} - {site_name}</title>
<link>{post_permalink}</link>
<description>{post_description}</description>
<guid isPermaLink="false">{guid}</guid>
<pubDate>{post_pubdate}</pubDate>
</item>
"""

            # Close the RSS channel
            rss_feed += """
</channel>
</rss>
"""

            # Output RSS feed to /feed/index.xml
            rss_output_dir = os.path.join(self.output_dir, 'feed')
            os.makedirs(rss_output_dir, exist_ok=True)
            rss_output_file = os.path.join(rss_output_dir, 'index.xml')

            with open(rss_output_file, 'w') as f:
                f.write(rss_feed)

            self.logger.info(f"Generated RSS feed at {rss_output_file}")

        except Exception as e:
            self.logger.error(f"Failed to generate RSS feed: {e}")

    def generate_xml_sitemap(self, site_url):
        """Generate a proper XML sitemap."""
        try:
            # Ensure the site_url ends with a '/'
            if not site_url.endswith('/'):
                site_url += '/'

            # Collect entries for the sitemap
            sitemap_entries = []

            # Add the homepage
            sitemap_entries.append(self.format_xml_sitemap_entry(site_url, datetime.now()))

            # Add URLs for posts
            for post in self.posts:
                post_permalink = f"{site_url.rstrip('/')}/{post.get('permalink', '')}"
                post_date_str = post.get('date', datetime.now())

                # Try multiple formats for the post date
                if isinstance(post_date_str, str):
                    date_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%b %d, %Y']
                    post_date = None
                    for fmt in date_formats:
                        try:
                            post_date = datetime.strptime(post_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    if post_date is None:
                        self.logger.error(f"Date '{post_date_str}' could not be parsed with any known format. Using current date.")
                        post_date = datetime.now()
                elif isinstance(post_date_str, datetime):
                    post_date = post_date_str
                else:
                    post_date = datetime.now()

                sitemap_entries.append(self.format_xml_sitemap_entry(post_permalink, post_date))

            # Add URLs for pages
            for page in self.pages:
                page_permalink = f"{site_url.rstrip('/')}/{page.get('permalink', '')}"
                page_date = datetime.now()  # Adjust this as necessary for your requirements
                sitemap_entries.append(self.format_xml_sitemap_entry(page_permalink, page_date))

            # Generate the full XML sitemap content
            sitemap_xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {''.join(sitemap_entries)}
</urlset>
"""
            # Write the XML sitemap to output/sitemap.xml
            sitemap_output_file = os.path.join(self.output_dir, 'sitemap.xml')
            with open(sitemap_output_file, 'w', encoding='utf-8') as f:
                f.write(sitemap_xml_content)

            self.logger.info(f"XML Sitemap generated at {sitemap_output_file}")

        except Exception as e:
            self.logger.error(f"Failed to generate XML sitemap: {e}")

    def format_xml_sitemap_entry(self, url, lastmod):
        """Format a URL entry for the XML sitemap."""
        escaped_url = escape(url)
        
        # If lastmod is already a datetime, convert to the desired format
        if isinstance(lastmod, datetime):
            lastmod_str = lastmod.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(lastmod, str):
            # Attempt each format until one is successful
            date_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%b %d, %Y']
            lastmod_str = None
            for fmt in date_formats:
                try:
                    lastmod_dt = datetime.strptime(lastmod, fmt)
                    lastmod_str = lastmod_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    self.logger.info(f"Successfully parsed date '{lastmod}' with format '{fmt}'")
                    break
                except ValueError as e:
                    self.logger.debug(f"Failed to parse date '{lastmod}' with format '{fmt}': {e}")
            
            # If no format matches, log the fallback
            if lastmod_str is None:
                self.logger.error(f"Date '{lastmod}' could not be parsed with any known format. Using current date instead.")
                lastmod_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            lastmod_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        return f'''
    <url>
        <loc>{escaped_url}</loc>
        <lastmod>{lastmod_str}</lastmod>
    </url>
    '''

    def generate_robots_txt(self, mode="public"):
        """Generate a robots.txt file with public or private settings."""
        try:
            # Prepare robots.txt content based on mode
            if mode == "private":
                robots_txt_content = "User-agent: *\nDisallow: /"
                self.logger.info("Generated private robots.txt (Disallow all)")
            elif mode == "public":
                if self.site_url:  # Only generate the public robots.txt if site_url is provided
                    robots_txt_content = f"""User-agent: *
Allow: /

# Sitemap URL
Sitemap: {self.site_url.rstrip('/')}/sitemap.xml
"""
                    self.logger.info("Generated public robots.txt (Allow all)")
                else:
                    self.logger.warning("Public robots.txt requires site_url. Skipping creation.")
                    return
            else:
                self.logger.warning(f"Unknown robots.txt mode '{mode}'. Skipping creation.")
                return

            # Write robots.txt to the output directory
            robots_txt_path = os.path.join(self.output_dir, 'robots.txt')
            with open(robots_txt_path, 'w') as robots_file:
                robots_file.write(robots_txt_content)
            self.logger.info(f"robots.txt written to {robots_txt_path}")
        except Exception as e:
            self.logger.error(f"Failed to generate robots.txt: {e}")

    def build_404_page(self):
        """Build and generate the 404 error page for GitHub Pages."""
        try:
            # Define the path for the 404 page in the root of the output directory
            output_file_path = os.path.join(self.output_dir, '404.html')

            # Render the 404 page using the 404 template
            rendered_html = self.render_template(
                '404.html',
                title="Page Not Found",
                content="<p>The page you are looking for does not exist.</p>",
                relative_path='./',
                page={}  # Provide an empty page context
            )

            # Write the rendered 404 HTML to the root directory
            with open(output_file_path, 'w') as output_file:
                output_file.write(rendered_html)

            self.logger.info(f"Generated 404 page at {output_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to generate 404 page: {e}")

    def build(self):
        """Main method to generate the static site."""
        self.logger.info("Starting build process...")
        build_start_time = time.time()
        self.create_output_dir()

        # Download fonts
        self.download_fonts()

        # Build posts and pages
        self.build_posts_and_pages()

        # Build additional pages (index, static pages)
        self.build_index_page()

        # Build the 404 page
        self.build_404_page()

        # Generate robots.txt based on the flag
        self.generate_robots_txt(mode=getattr(args, 'robots', 'public'))

        # Minify assets if --minify is enabled
        if getattr(args, 'minify', False):
            self.minify_assets()

        build_end_time = time.time()
        total_time = build_end_time - build_start_time
        self.logger.info(f"Site build completed successfully in {total_time:.6f} seconds.")
        self.logger.info(f"Total posts generated: {self.posts_generated}")
        self.logger.info(f"Total pages generated: {self.pages_generated}")
        self.logger.info(f"Total images converted to WebP: {self.image_conversion_count}")

def resolve_output_path(output_dir):
    # If the output path starts with "~/", expand it to the user's home directory
    if output_dir.startswith("~/"):
        output_dir = os.path.expanduser(output_dir)
    return output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stattic - Static Site Generator')
    parser.add_argument('--output', type=str, default='output', help='Specify the output directory')
    parser.add_argument('--content', type=str, default='content', help='Specify the content directory')
    parser.add_argument('--templates', type=str, help='Specify the templates directory (default: templates/)')
    parser.add_argument('--assets', type=str, help='Specify a custom assets directory to include in the build')
    parser.add_argument('--posts-per-page', type=int, default=5, help='Number of posts per index page')
    parser.add_argument('--sort-by', type=str, choices=['date', 'title', 'author'], default='date', help='Sort posts by date, title, or author')
    parser.add_argument('--fonts', type=str, help='Comma-separated list of Google Fonts to download')
    parser.add_argument('--site-url', type=str, help='Specify the site URL for production builds')
    parser.add_argument('--robots', type=str, choices=['public', 'private'], default='public', help="Generate a public or private robots.txt file (default: public)")
    parser.add_argument('--watch', action='store_true', help='Enable watch mode to automatically rebuild on file changes')
    parser.add_argument('--minify', action='store_true', help='Minify CSS and JS into single files')

    args = parser.parse_args()

    # Resolve the output directory path
    output_dir = resolve_output_path(args.output)

    # Use the provided templates directory or default to 'templates/'
    templates_dir = args.templates if args.templates else os.path.join(os.path.dirname(__file__), 'templates')

    # Use the provided assets directory if specified
    assets_dir = args.assets

    # Parse fonts
    fonts = [font.strip() for font in args.fonts.split(',')] if args.fonts else None

    # Create a generator with the specified directories, output, and settings
    generator = Stattic(
        content_dir=args.content,
        templates_dir=templates_dir,
        output_dir=output_dir,
        posts_per_page=args.posts_per_page,
        sort_by=args.sort_by,
        fonts=fonts,
        site_url=args.site_url,
        assets_dir=assets_dir
    )

    generator.build()

    # Generate RSS and sitemap only if site_url is provided (production mode)
    if generator.site_url:
        generator.generate_rss_feed(generator.site_url)
        generator.generate_xml_sitemap(generator.site_url)
    else:
        generator.logger.info("Skipping RSS feed and XML sitemap generation (not in production mode).")
