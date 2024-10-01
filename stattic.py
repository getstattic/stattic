import os
import shutil
import markdown
import yaml
import argparse
import logging
import time
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
import re
import requests
from PIL import Image
import csscompressor
import rjsmin

GOOGLE_FONTS_API = 'https://fonts.googleapis.com/css2?family={font_name}:wght@{weights}&display=swap'

class Stattic:
    def __init__(self, content_dir='content', templates_dir='templates', output_dir='output', posts_per_page=5, sort_by='date', fonts=None):
        self.content_dir = content_dir
        self.posts_dir = os.path.join(content_dir, 'posts')
        self.pages_dir = os.path.join(content_dir, 'pages')
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, 'images')  # Images directory for downloads
        self.assets_src_dir = os.path.join(os.path.dirname(__file__), 'assets')  # Local assets folder
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

        # Setup logging (now logs are stored in the /logs/ folder)
        log_file = self.setup_logging()

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
        """Convert markdown text to HTML."""
        return markdown.markdown(text)

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

        self.logger = logger
        self.logger.info(f"Logging initialized. Logs stored at {log_file}")

        return log_file

    def minify_assets(self):
        """Minify all CSS and JS files into single files."""
        try:
            # Paths to CSS and JS files
            css_dir = os.path.join(self.assets_output_dir, 'css')
            js_dir = os.path.join(self.assets_output_dir, 'js')

            # Output paths for minified files
            minified_css_path = os.path.join(css_dir, 'main.min.css')
            minified_js_path = os.path.join(js_dir, 'main.min.js')

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

    def format_date(self, date_str):
        """Format the date from 'YYYY-MM-DDTHH:MM:SS' to 'Month DD, YYYY'."""
        try:
            # If date_str is already a datetime.date or datetime.datetime object, format it directly
            if isinstance(date_str, (datetime, datetime.date)):
                return date_str.strftime('%B %d, %Y')

            # Parse the input string to a datetime object if it's a string
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            return date_obj.strftime('%B %d, %Y')

        except (ValueError, TypeError):
            # Return the original string if formatting fails or if it's not a string/datetime
            return date_str

    def load_categories_and_tags(self):
        """Load categories and tags from YAML files."""
        try:
            with open(os.path.join(self.content_dir, 'categories.yml'), 'r') as cat_file:
                self.categories = yaml.safe_load(cat_file)
            with open(os.path.join(self.content_dir, 'tags.yml'), 'r') as tag_file:
                self.tags = yaml.safe_load(tag_file)
            self.logger.info(f"Loaded {len(self.categories)} categories and {len(self.tags)} tags")
        except FileNotFoundError as e:
            self.logger.error(f"YAML file not found: {e}")
        except Exception as e:
            self.logger.error(f"Error loading categories/tags: {e}")

    def load_authors(self):
        """Load authors from a YAML file."""
        try:
            with open(os.path.join(self.content_dir, 'authors.yml'), 'r') as authors_file:
                self.authors = yaml.safe_load(authors_file)
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

                # Fix title extraction if it's a dictionary with 'rendered'
                title = metadata.get('title', 'Untitled')
                if isinstance(title, dict):
                    title = title.get('rendered', 'Untitled')

                # Add page metadata to self.pages
                self.pages.append({
                    'title': title,
                    'permalink': f"/{metadata.get('custom_url', page_file.replace('.md', ''))}/"
                })

            self.logger.info(f"Loaded {len(self.pages)} pages for navigation")

        except Exception as e:
            self.logger.error(f"Failed to load pages: {e}")

    def download_image(self, url, output_dir):
        """Download an image and save it locally."""
        try:
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
            fonts_css_path = os.path.join(self.assets_output_dir, 'css/fonts.css')
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

                    # Download the CSS from Google Fonts for each weight
                    response = requests.get(google_font_url)
                    if response.status_code == 200:
                        css_data = response.text

                        # Extract URLs and font formats from the CSS data
                        font_urls = re.findall(r'url\((.*?)\) format\((.*?)\);', css_data)

                        for font_url, format_type in font_urls:
                            # Ensure the extension matches the format (woff2 is preferred)
                            file_extension = 'woff2' if 'woff2' in format_type else 'ttf'
                            font_output_file = os.path.join(fonts_output_path, f"{font.strip().lower()}-{weight}.{file_extension}")

                            # Download the actual font file
                            font_file_response = requests.get(font_url)
                            if font_file_response.status_code == 200:
                                with open(font_output_file, 'wb') as f:
                                    f.write(font_file_response.content)
                                self.logger.info(f"Downloaded {font} ({weight}) from {font_url}")

                                # Generate @font-face rule with unique font-family name for each weight
                                css_content += f"""
@font-face {{
  font-family: '{font}-{weight}';  /* Unique font family for each weight */
  font-style: normal;
  font-weight: {weight};
  font-display: swap;
  src: url('../fonts/{os.path.basename(font_output_file)}') format({format_type});
}}
"""

                                # Generate custom class using the unique font-family name
                                css_content += f"""
.{font.strip().lower()}-{weight} {{
  font-family: '{font}-{weight}', 'Helvetica', 'Arial', sans-serif;
  font-weight: {weight};
}}
"""
                            else:
                                self.logger.error(f"Failed to download font file from {font_url}")
                    else:
                        self.logger.error(f"Failed to fetch font CSS from Google Fonts for {font} weight {weight}")

            # Write the @font-face rules, custom classes, and body CSS to the fonts.css file
            with open(fonts_css_path, 'w') as f:
                f.write(css_content)

            self.logger.info(f"Downloaded fonts and generated CSS: {', '.join(self.fonts)}")
        except Exception as e:
            self.logger.error(f"Failed to download fonts: {e}")

    def copy_assets_to_output(self):
        """Copy the local assets folder (CSS, JS, etc.) to the output directory."""
        try:
            if os.path.exists(self.assets_src_dir):
                # Copy the entire assets directory to the output directory
                shutil.copytree(self.assets_src_dir, self.assets_output_dir, dirs_exist_ok=True)
                self.logger.info(f"Copied assets to {self.assets_output_dir}")
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
        """Find all image URLs in the content, download, and convert them."""
        image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)  # Extract image URLs from markdown
        local_image_paths = {}

        for url in image_urls:
            self.logger.info(f"Processing image: {url}")
            image_name = os.path.basename(url)
            webp_image_path = os.path.join(self.images_dir, image_name.rsplit('.', 1)[0] + '.webp')

            # Check if the WebP version already exists
            if os.path.exists(webp_image_path):
                self.logger.info(f"Using existing WebP image: {webp_image_path}")
                local_image_paths[url] = os.path.join('/images', os.path.basename(webp_image_path))
            else:
                # Download and convert the image if the WebP version does not exist
                image_path = self.download_image(url, self.images_dir)
                if image_path:
                    webp_path = self.convert_image_to_webp(image_path)
                    if webp_path:
                        local_image_paths[url] = os.path.join('/images', os.path.basename(webp_path))

        # Replace external URLs with local WebP paths in the content
        for url, webp_path in local_image_paths.items():
            content = content.replace(url, webp_path)

        return content

    def parse_markdown_with_metadata(self, filepath):
        """Extract frontmatter and markdown content from the file, process images."""
        try:
            start_time = time.time()
            with open(filepath, 'r') as f:
                content = f.read()

            # Split frontmatter (YAML) and markdown body
            if content.startswith('---'):
                frontmatter, markdown_content = content.split('---', 2)[1:]
                metadata = yaml.safe_load(frontmatter)
            else:
                metadata = {}
                markdown_content = content

            # Process and download images from the markdown content
            markdown_content = self.process_images(markdown_content)

            duration = time.time() - start_time
            self.logger.info(f"Parsed markdown file: {filepath} (Time taken: {duration:.2f} seconds)")
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
            self.logger.info(f"Found {len(files)} markdown files in {directory} (Time taken: {duration:.2f} seconds)")
            return files
        except FileNotFoundError as e:
            self.logger.error(f"Directory not found: {directory}")
            raise

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
            formatted_date = self.format_date(metadata.get('date', ''))

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

            # Get the template part from the frontmatter
            template_part = metadata.get('template', 'default')
            
            # Construct the full template name dynamically, e.g., post-about.html
            template_name = f"post-{template_part}.html" if not is_page else f"page-{template_part}.html"

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
                metadata=metadata
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
            context['minify'] = args.minify  # Pass the minify flag
            rendered_template = template.render(context)
            duration = time.time() - start_time
            self.logger.info(f"Rendered template: {template_name} (Time taken: {duration:.2f} seconds)")
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
            post_output_dir = os.path.join(self.output_dir, 'posts', post_slug)

            # Render the post and write it to the output directory
            self.build_post_or_page(metadata, html_content, post_slug, post_output_dir, is_page=False)

            # Collect post metadata for the index page
            post_metadata = {
                'title': metadata.get('title', 'Untitled'),
                'excerpt': metadata.get('excerpt', self.generate_excerpt(md_content)),
                'permalink': f"/posts/{post_slug}/",
                'date': metadata.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
            self.posts.append(post_metadata)

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
        return markdown.markdown(markdown_content)

    def generate_excerpt(self, content):
        """Generate an excerpt from the post content if no excerpt is provided."""
        words = content.split()[:30]  # Take the first 30 words
        return ' '.join(words) + '...'

    def build_index_page(self):
        """Render and build the index (homepage) with the list of posts."""
        try:
            # Sort posts by date, and limit them based on posts_per_page
            posts_for_index = sorted(self.posts, key=lambda post: post['date'], reverse=True)[:self.posts_per_page]

            # Render the index.html template with the list of posts and pages for the menu
            rendered_html = self.render_template('index.html', posts=posts_for_index, pages=self.pages)

            # Save the generated index page
            output_file_path = os.path.join(self.output_dir, 'index.html')
            with open(output_file_path, 'w') as output_file:
                output_file.write(rendered_html)

            self.logger.info(f"Generated index page: {output_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to generate index page: {e}")

    def build_static_pages(self):
        """Generate static pages like contact page."""
        # Example for a static contact page
        output_dir = os.path.join(self.output_dir, 'contact')
        os.makedirs(output_dir, exist_ok=True)
        rendered_html = self.render_template('page.html', title="Contact Us", content="<p>Contact page content</p>")
        with open(os.path.join(output_dir, 'index.html'), 'w') as output_file:
            output_file.write(rendered_html)
        self.logger.info(f"Generated contact page: {output_dir}")

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
        # self.build_static_pages()

        # Minify assets if --minify is enabled
        if args.minify:
            self.minify_assets()

        build_end_time = time.time()
        total_time = build_end_time - build_start_time
        self.logger.info(f"Site build completed successfully in {total_time:.2f} seconds.")
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
    parser.add_argument('--posts-per-page', type=int, default=5, help='Number of posts per index page')
    parser.add_argument('--sort-by', type=str, choices=['date', 'title', 'author'], default='date', help='Sort posts by date, title, or author')
    parser.add_argument('--fonts', type=str, help='Comma-separated list of Google Fonts to download')
    parser.add_argument('--watch', action='store_true', help='Enable watch mode to automatically rebuild on file changes')
    parser.add_argument('--minify', action='store_true', help='Minify CSS and JS into single files')

    args = parser.parse_args()

    # Resolve the output directory path
    output_dir = os.path.expanduser(args.output)

    # Parse fonts
    fonts = [font.strip() for font in args.fonts.split(',')] if args.fonts else None

    # Create a generator with the specified output directory, posts per page, sorting method, and fonts
    generator = Stattic(output_dir=output_dir, posts_per_page=args.posts_per_page, sort_by=args.sort_by, fonts=fonts)

    generator.build()
