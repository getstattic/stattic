import os
import markdown
import yaml
import argparse
import logging
import time
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Stattic:
    def __init__(self, content_dir='content', templates_dir='templates', pages_dir='pages', output_dir='output', posts_per_page=5, sort_by='date', log_file='stattic.log'):
        self.content_dir = content_dir
        self.templates_dir = templates_dir
        self.pages_dir = pages_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.posts = []  # To store metadata of all posts for index, archive, and RSS generation
        self.posts_per_page = posts_per_page
        self.sort_by = sort_by
        self.tags = {}  # To store posts by tag
        self.categories = {}  # To store posts by category

        # Setup logging
        self.logger = self.setup_logging(log_file)
        self.pages_generated = 0
        self.posts_generated = 0

    def setup_logging(self, log_file):
        """Setup the logger to write both to a file and the console."""
        logger = logging.getLogger('stattic')
        logger.setLevel(logging.DEBUG)

        # Create file handler which logs all messages
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        # Create console handler for higher level logs
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create a formatter and set it for the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

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

    def build_post(self, metadata, html_content, post_slug, output_dir):
        """Render the post or page template and write it to the output directory."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join(output_dir, 'index.html')

            # Check if it's a static page (use page.html template)
            is_page = 'date' not in metadata or metadata.get('type', '') == 'page'
            template_name = 'page.html' if is_page else 'post.html'

            rendered_html = self.render_template(
                template_name, 
                content=html_content, 
                title=metadata.get('title', 'Untitled'), 
                author=metadata.get('author', 'Unknown'),
                date=metadata.get('date', ''),
                categories=metadata.get('categories', []),
                tags=metadata.get('tags', []),
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

    def build_category_pages(self):
        """Generate category archive pages."""
        try:
            for category, posts in self.categories.items():
                category_slug = category.lower().replace(" ", "-")
                output_dir = os.path.join(self.output_dir, 'categories', category_slug)
                os.makedirs(output_dir, exist_ok=True)
                rendered_html = self.render_template('category.html', category=category, posts=posts)
                with open(os.path.join(output_dir, 'index.html'), 'w') as output_file:
                    output_file.write(rendered_html)
                self.logger.info(f"Generated category archive: {output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to generate category pages: {e}")

    def build_tag_pages(self):
        """Generate tag archive pages."""
        try:
            for tag, posts in self.tags.items():
                tag_slug = tag.lower().replace(" ", "-")
                output_dir = os.path.join(self.output_dir, 'tags', tag_slug)
                os.makedirs(output_dir, exist_ok=True)
                rendered_html = self.render_template('tag.html', tag=tag, posts=posts)
                with open(os.path.join(output_dir, 'index.html'), 'w') as output_file:
                    output_file.write(rendered_html)
                self.logger.info(f"Generated tag archive: {output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to generate tag pages: {e}")

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

        # Loop through each markdown file in the content directory
        try:
            for md_file in self.get_markdown_files(self.content_dir):
                filepath = os.path.join(self.content_dir, md_file)

                # Extract metadata and markdown content
                metadata, md_content = self.parse_markdown_with_metadata(filepath)

                # Skip drafts
                if metadata.get('draft', False):
                    self.logger.info(f"Skipping draft: {md_file}")
                    continue

                # Convert markdown content to HTML
                html_content = self.convert_markdown_to_html(md_content)

                # Get the language for the post
                lang = metadata.get('lang', 'en')

                # Determine the output directory for the post
                custom_url = metadata.get('custom_url')
                if custom_url:
                    post_slug = custom_url
                    post_dir = os.path.join(self.output_dir, lang, custom_url)
                else:
                    post_slug = md_file.replace('.md', '')
                    post_dir = os.path.join(self.output_dir, lang, 'posts', post_slug)

                # Generate an excerpt if none is provided
                excerpt = metadata.get('excerpt', self.generate_excerpt(md_content))

                # Collect post info for the index, archive, and tag/category pages
                post_info = {
                    'title': metadata.get('title', 'Untitled'),
                    'author': metadata.get('author', 'Unknown'),
                    'date': metadata.get('date', ''),
                    'categories': metadata.get('categories', []),
                    'tags': metadata.get('tags', []),
                    'featured_image': metadata.get('featured_image', None),
                    'excerpt': excerpt,
                    'permalink': f'{lang}/{custom_url or f"posts/{post_slug}/index.html"}',
                    'content': html_content,
                    'metadata': metadata,  # Include all custom metadata
                    'seo_title': metadata.get('seo_title', metadata.get('title', 'Untitled')),
                    'keywords': metadata.get('keywords', ''),
                    'description': metadata.get('description', ''),
                    'lang': lang
                }

                self.posts.append(post_info)

                # Add post to tags
                for tag in post_info['tags']:
                    if tag not in self.tags:
                        self.tags[tag] = []
                    self.tags[tag].append(post_info)

                # Add post to categories
                for category in post_info['categories']:
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(post_info)

                # Render the post and write it to the output directory with pretty permalinks or custom URL
                self.build_post(metadata, html_content, post_slug, post_dir)

            # Build additional pages (index, category archives, tag archives, static pages)
            self.build_index_page()
            self.build_category_pages()
            self.build_tag_pages()
            self.build_static_pages()

        except Exception as e:
            self.logger.error(f"Error occurred during site generation: {e}")
            raise

        build_end_time = time.time()
        total_time = build_end_time - build_start_time
        self.logger.info(f"Site build completed successfully in {total_time:.2f} seconds.")
        self.logger.info(f"Total posts generated: {self.posts_generated}")
        self.logger.info(f"Total pages generated: {self.pages_generated}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stattic - Static Site Generator')
    parser.add_argument('--output', type=str, default='output', help='Specify the output directory')
    parser.add_argument('--posts-per-page', type=int, default=5, help='Number of posts per index page')
    parser.add_argument('--sort-by', type=str, choices=['date', 'title', 'author'], default='date', help='Sort posts by date, title, or author')
    parser.add_argument('--watch', action='store_true', help='Enable watch mode to automatically rebuild on file changes')

    args = parser.parse_args()

    # Create a generator with the specified output directory, posts per page, and sorting method
    generator = Stattic(output_dir=args.output, posts_per_page=args.posts_per_page, sort_by=args.sort_by)

    generator.build()
