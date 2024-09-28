import os
import requests
import yaml
import argparse
import html2text
from datetime import datetime

# Output directory for Markdown files
CONTENT_DIR = "content"

# Ensure content directory exists
if not os.path.exists(CONTENT_DIR):
    os.makedirs(CONTENT_DIR)

# Initialize html2text converter
html_converter = html2text.HTML2Text()
html_converter.ignore_images = False  # Allow image links
html_converter.ignore_links = False   # Allow hyperlinks
html_converter.body_width = 0         # Preserve line breaks in Markdown

def fetch_wordpress_data(domain_url, endpoint, per_page=100):
    """Fetch paginated data from the WordPress REST API."""
    data = []
    page = 1

    while True:
        url = f"{domain_url}/wp-json/wp/v2/{endpoint}?per_page={per_page}&page={page}&_embed"
        response = requests.get(url)

        # Check if the response is empty or not a valid JSON response
        try:
            response.raise_for_status()
            items = response.json()

            if not items:  # No data returned
                print(f"No data found at {url}")
                break

            data.extend(items)
            
            # If fewer items than `per_page` are returned, we reached the end
            if len(items) < per_page:
                break

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {url}")
            break
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err} - {url}")
            break
        except Exception as err:
            print(f"Other error occurred: {err} - {url}")
            break

        page += 1

    return data

def save_as_markdown(file_path, frontmatter, content):
    """Save data as a Markdown file with YAML frontmatter."""
    with open(file_path, "w") as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, allow_unicode=True)
        f.write("---\n")
        f.write(content)

def convert_post_to_md(post, post_type="post"):
    """Convert WordPress post or page to Markdown."""
    title = post.get('title', {}).get('rendered', 'Untitled')
    author = post.get('_embedded', {}).get('author', [{}])[0].get('name', 'Unknown')
    date = post.get('date', '')
    slug = post.get('slug', '')
    
    # Convert HTML content and excerpt to Markdown
    html_content = post.get('content', {}).get('rendered', '')
    content = html_converter.handle(html_content)  # Convert to Markdown
    
    html_excerpt = post.get('excerpt', {}).get('rendered', '')
    excerpt = html_converter.handle(html_excerpt).strip()  # Convert to Markdown

    # Extract categories and tags if available
    categories = post.get('categories', [])
    tags = post.get('tags', [])

    # Define frontmatter for the markdown file
    frontmatter = {
        'title': title,
        'author': author,
        'date': date,
        'categories': categories,
        'tags': tags,
        'excerpt': excerpt,
        'custom_url': slug,
        'type': post_type  # 'post' or 'page'
    }

    # Define the file path based on the post type and slug
    file_dir = os.path.join(CONTENT_DIR, f"{post_type}s")
    os.makedirs(file_dir, exist_ok=True)

    file_path = os.path.join(file_dir, f"{slug}.md")

    # Save the post content as a markdown file
    save_as_markdown(file_path, frontmatter, content)
    print(f"Saved {post_type}: {file_path}")

def save_posts_and_pages(domain_url):
    """Fetch and save all posts and pages as markdown files."""
    print("Fetching all posts...")
    posts = fetch_wordpress_data(domain_url, "posts")

    print(f"Total posts fetched: {len(posts)}")

    print("Fetching all pages...")
    pages = fetch_wordpress_data(domain_url, "pages")

    print(f"Total pages fetched: {len(pages)}")

    # Save each post as markdown
    for post in posts:
        convert_post_to_md(post, post_type="post")

    # Save each page as markdown
    for page in pages:
        convert_post_to_md(page, post_type="page")

def save_categories_and_tags(domain_url):
    """Fetch and save all categories and tags as markdown metadata."""
    print("Fetching categories...")
    categories = fetch_wordpress_data(domain_url, "categories")
    print(f"Total categories fetched: {len(categories)}")

    print("Fetching tags...")
    tags = fetch_wordpress_data(domain_url, "tags")
    print(f"Total tags fetched: {len(tags)}")

    # Save categories as a YAML metadata file
    categories_path = os.path.join(CONTENT_DIR, "categories.yml")
    with open(categories_path, "w") as f:
        yaml.dump(categories, f, allow_unicode=True)
    print(f"Saved categories metadata: {categories_path}")

    # Save tags as a YAML metadata file
    tags_path = os.path.join(CONTENT_DIR, "tags.yml")
    with open(tags_path, "w") as f:
        yaml.dump(tags, f, allow_unicode=True)
    print(f"Saved tags metadata: {tags_path}")

if __name__ == "__main__":
    # Use argparse to require domain URL as input
    parser = argparse.ArgumentParser(description="Fetch WordPress data and convert to Markdown")
    parser.add_argument('domain', type=str, help="The WordPress site URL (e.g., https://your-site.com)")

    args = parser.parse_args()
    domain_url = args.domain.rstrip("/")  # Ensure no trailing slash

    # Fetch and save posts, pages, categories, and tags
    save_posts_and_pages(domain_url)
    save_categories_and_tags(domain_url)
