import os
import markdown
import yaml
import argparse
import logging
import time
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError

class Stattic:
    def __init__(self, content_dir='content', templates_dir='templates', output_dir='output', posts_per_page=5, sort_by='date'):
        self.content_dir = content_dir
        self.posts_dir = os.path.join(content_dir, 'posts')
        self.pages_dir = os.path.join(content_dir, 'pages')
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.posts = []  # Store metadata of all posts for index, archive, and RSS generation
        self.pages_generated = 0
        self.posts_generated = 0
        self.posts_per_page = posts_per_page
        self.sort_by = sort_by
        self.categories = {}
        self.tags = {}

        # Setup logging (now logs are stored in the /logs/ folder)
        log_file = self.setup_logging()

        # Load categories and tags from YAML files
        self.load_categories_and_tags()

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

    def setup_logging(self):
        """Setup the logger to write both to a file and the console."""
        # Define the logs directory relative to the script location
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)  # Create the logs directory if it doesn't exist

        # Create a log file name with the current date and time
        log_file = os.path.join(logs_dir, f"stattic_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

        # Setup logger
        logger = logging.getLogger('stattic')
        logger.setLevel(logging.DEBUG)

        # Create file handler which logs all messages
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        # Create console handler for higher-level logs
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create a formatter and set it for the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        self.logger = logger
        self.logger.info(f"Logging initialized. Logs stored at {log_file}")

        return log_file

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

    def parse_markdown_with_metadata(self, filepath):
        """Extract frontmatter and markdown content from the file."""
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

            duration = time.time() - start_time
            self.logger.info(f"Parsed markdown file: {filepath} (Time taken: {duration:.2f} seconds)")
            return metadata, markdown_content
        except Exception as e:
            self.logger.error(f"Failed to parse markdown file: {filepath} - {e}")
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

    def convert_markdown_to_html(self, markdown_content):
        """Convert Markdown content to HTML."""
        return markdown.markdown(markdown_content)

    def generate_excerpt(self, content):
        """Generate an excerpt from the post content if no excerpt is provided."""
        words = content.split()[:30]  # Take the first 30 words
        return ' '.join(words) + '...'

    def build_post_or_page(self, metadata, html_content, post_slug, output_dir, is_page=False):
        """Render the post or page template and write it to the output directory."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join(output_dir, 'index.html')

            # Use the correct template (post or page)
            template_name = 'page.html' if is_page else 'post.html'

            # Map category and tag IDs to names
            post_categories = [cat['name'] for cat in self.categories if cat['id'] in metadata.get('categories', [])]
            post_tags = [tag['name'] for tag in self.tags if tag['id'] in metadata.get('tags', [])]

            rendered_html = self.render_template(
                template_name,
                content=html_content,
                title=metadata.get('title', 'Untitled'),
                author=metadata.get('author', 'Unknown'),
                date=metadata.get('date', ''),
                categories=post_categories,
                tags=post_tags,
                featured_image=metadata.get('featured_image', None),
                seo_title=metadata.get('seo_title', metadata.get('title', 'Untitled')),
                seo_keywords=metadata.get('keywords', ''),
                seo_description=metadata.get('description', ''),
                lang=metadata.get('lang', 'en'),
                metadata=metadata  # Pass all metadata to the template
            )

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

    def build_index_page(self):
        """Render and build the index (homepage) with the list of posts."""
        try:
            output_dir = os.path.join(self.output_dir, 'index.html')
            rendered_html = self.render_template('index.html', posts=self.posts)
            with open(output_dir, 'w') as output_file:
                output_file.write(rendered_html)
            self.logger.info(f"Generated index page: {output_dir}")
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
    output_dir = resolve_output_path(args.output)

    # Create a generator with the specified output directory, posts per page, and sorting method
    generator = Stattic(output_dir=output_dir, posts_per_page=args.posts_per_page, sort_by=args.sort_by)

    generator.build()
