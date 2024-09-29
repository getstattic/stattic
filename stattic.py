import os
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

class Stattic:
    def __init__(self, content_dir='content', templates_dir='templates', output_dir='output', posts_per_page=5, sort_by='date'):
        self.content_dir = content_dir
        self.posts_dir = os.path.join(content_dir, 'posts')
        self.pages_dir = os.path.join(content_dir, 'pages')
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, 'images')  # Images directory for downloads
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.posts = []  # Store metadata of all posts for index, archive, and RSS generation
        self.pages = []  # Track pages for navigation
        self.pages_generated = 0
        self.posts_generated = 0
        self.posts_per_page = posts_per_page
        self.sort_by = sort_by
        self.categories = {}
        self.tags = {}
        self.image_conversion_count = 0  # Track total number of converted images

        # Setup logging (now logs are stored in the /logs/ folder)
        log_file = self.setup_logging()

        # Load categories and tags from YAML files
        self.load_categories_and_tags()

        # Ensure images directory exists
        os.makedirs(self.images_dir, exist_ok=True)

        # Ensure pages are loaded before generating posts or pages
        self.load_pages()

    def load_categories_and_tags(self):
        """Load categories and tags from YAML files."""
        try:
            with open(os.path.join(self.content_dir, 'categories.yml'), 'r') as cat_file:
                self.categories = yaml.safe_load(cat_file)
                if isinstance(self.categories, list):
                    self.categories = {cat['id']: cat for cat in self.categories if isinstance(cat, dict) and 'id' in cat}
            with open(os.path.join(self.content_dir, 'tags.yml'), 'r') as tag_file:
                self.tags = yaml.safe_load(tag_file)
                if isinstance(self.tags, list):
                    self.tags = {tag['id']: tag for tag in self.tags if isinstance(tag, dict) and 'id' in tag}
            self.logger.info(f"Loaded {len(self.categories)} categories and {len(self.tags)} tags")
        except FileNotFoundError as e:
            self.logger.error(f"YAML file not found: {e}")
        except Exception as e:
            self.logger.error(f"Error loading categories/tags: {e}")

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

    def create_output_dir(self):
        """Create the output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Created output directory: {self.output_dir}")

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

            post_categories = []
            for cat_id in metadata.get('categories', []):
                if isinstance(cat_id, int):
                    category = self.categories.get(cat_id, {})
                    post_categories.append(category.get('name', f"Unknown (ID: {cat_id})"))
                else:
                    self.logger.error(f"Invalid category ID: {cat_id}")

            post_tags = []
            for tag_id in metadata.get('tags', []):
                if isinstance(tag_id, int):
                    tag = self.tags.get(tag_id, {})
                    post_tags.append(tag.get('name', f"Unknown (ID: {tag_id})"))
                else:
                    self.logger.error(f"Invalid tag ID: {tag_id}")

            rendered_html = self.render_template(
                'page.html' if is_page else 'post.html',
                content=html_content,
                title=title,
                author=metadata.get('author', 'Unknown'),
                date=metadata.get('date', ''),
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
                'date': metadata.get('date', 'Unknown')
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

        # Build posts and pages
        self.build_posts_and_pages()

        # Build additional pages (index, static pages)
        self.build_index_page()
        self.build_static_pages()

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
    parser.add_argument('--watch', action='store_true', help='Enable watch mode to automatically rebuild on file changes')

    args = parser.parse_args()

    # Resolve the output directory path
    output_dir = os.path.expanduser(args.output)

    # Create a generator with the specified output directory, posts per page, and sorting method
    generator = Stattic(output_dir=output_dir, posts_per_page=args.posts_per_page, sort_by=args.sort_by)

    generator.build()
