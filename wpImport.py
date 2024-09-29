import os
import requests
import yaml
import argparse
import html2text
from datetime import datetime
from tqdm import tqdm  # For progress bar

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
                tqdm.write(f"No data found at {url}")
                break

            data.extend(items)
            
            # If fewer items than `per_page` are returned, we reached the end
            if len(items) < per_page:
                break

        except requests.exceptions.HTTPError as http_err:
            tqdm.write(f"HTTP error occurred: {http_err} - {url}")
            break
        except requests.exceptions.JSONDecodeError as json_err:
            tqdm.write(f"JSON decode error: {json_err} - {url}")
            break
        except Exception as err:
            tqdm.write(f"Other error occurred: {err} - {url}")
            break

        page += 1

    return data

def map_term_ids_to_names(ids, terms):
    """Map a list of term IDs to their names."""
    return [terms.get(term_id, {'id': term_id, 'name': f"Unknown (ID: {term_id})"})['name'] for term_id in ids]

def save_as_markdown(file_path, frontmatter, content):
    """Save data as a Markdown file with YAML frontmatter."""
    # Ensure title is a string, not a dictionary
    if 'title' in frontmatter and isinstance(frontmatter['title'], dict):
        frontmatter['title'] = frontmatter['title'].get('rendered', 'Untitled')

    with open(file_path, "w") as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, allow_unicode=True, sort_keys=False)  # Ensure the order remains
        f.write("---\n")
        f.write(content)

def convert_post_to_md(post, authors, categories, tags, custom_taxonomies, post_type="post"):
    """Convert WordPress post or page to Markdown."""
    slug = post.get('slug', 'untitled')
    
    # Convert HTML content and excerpt to Markdown
    html_content = post.get('content', {}).get('rendered', '')
    content = html_converter.handle(html_content)  # Convert to Markdown
    
    # Get author name using author ID
    author_id = post.get('author', 0)
    author_name = authors.get(author_id, "Unknown")

    # Extract the title properly from the rendered field
    title = post.get('title', {}).get('rendered', 'Untitled')

    # Define the most important frontmatter elements first
    frontmatter = {
        'title': title,  # Correct title extraction
        'date': post.get('date', ''),
        'author': author_name,
        'excerpt': html_converter.handle(post.get('excerpt', {}).get('rendered', '')).strip(),
        'custom_url': post.get('slug', ''),
        'type': post_type  # 'post' or 'page'
    }

    # Map categories and tags by ID to their names
    frontmatter['categories'] = map_term_ids_to_names(post.get('categories', []), categories)
    frontmatter['tags'] = map_term_ids_to_names(post.get('tags', []), tags)

    # Add ACF data if available
    acf_data = post.get('acf', None)
    if acf_data:
        frontmatter['acf'] = acf_data

    # Add custom taxonomies
    for taxonomy, terms in custom_taxonomies.items():
        if taxonomy in post:
            frontmatter[taxonomy] = map_term_ids_to_names(post.get(taxonomy, []), terms)

    # Add any other remaining metadata, excluding unnecessary fields
    filtered_metadata = {k: v for k, v in post.items() if k not in ['content', 'excerpt', 'guid', '_links', '_embedded', 'acf']}
    frontmatter.update(filtered_metadata)

    # Define the file path based on the post type and slug
    file_dir = os.path.join(CONTENT_DIR, f"{post_type}s")
    os.makedirs(file_dir, exist_ok=True)

    file_path = os.path.join(file_dir, f"{slug}.md")

    # Save the post content as a markdown file
    save_as_markdown(file_path, frontmatter, content)
    tqdm.write(f"Saved {post_type}: {file_path}")

def fetch_terms_by_taxonomy(domain_url, taxonomy):
    """Fetch terms for a specific taxonomy (e.g., categories, tags, custom taxonomies)."""
    terms = fetch_wordpress_data(domain_url, taxonomy)
    # Ensure the term data has both 'id' and 'name' keys for each term
    return {term['id']: {'id': term['id'], 'name': term['name']} for term in terms}

def fetch_custom_taxonomies(domain_url):
    """Fetch all available custom taxonomies from the WordPress REST API."""
    url = f"{domain_url}/wp-json/wp/v2/taxonomies"
    response = requests.get(url)

    try:
        response.raise_for_status()
        taxonomies = response.json()

        # Filter custom taxonomies by checking if they are not "category" or "post_tag"
        custom_taxonomies = {key: val for key, val in taxonomies.items() if key not in ['category', 'post_tag']}
        
        # Now fetch terms for each custom taxonomy
        taxonomy_terms = {}
        for taxonomy in custom_taxonomies.keys():
            terms_url = f"{domain_url}/wp-json/wp/v2/{taxonomy}?per_page=100"
            try:
                taxonomy_terms[taxonomy] = fetch_terms_by_taxonomy(domain_url, taxonomy)
            except requests.exceptions.HTTPError as http_err:
                tqdm.write(f"HTTP error occurred: {http_err} - {terms_url}")
                continue  # Skip this taxonomy if 404 or any other error occurs

        return taxonomy_terms

    except requests.exceptions.HTTPError as http_err:
        tqdm.write(f"HTTP error occurred while fetching taxonomies: {http_err}")
    except requests.exceptions.JSONDecodeError as json_err:
        tqdm.write(f"JSON decode error while fetching taxonomies: {json_err}")
    except Exception as err:
        tqdm.write(f"Other error occurred while fetching taxonomies: {err}")

    return {}

def save_posts_and_pages(domain_url, authors, categories, tags, custom_taxonomies):
    """Fetch and save all posts and pages as markdown files."""
    print("Fetching all posts...")
    posts = fetch_wordpress_data(domain_url, "posts")

    print(f"Total posts fetched: {len(posts)}")

    print("Fetching all pages...")
    pages = fetch_wordpress_data(domain_url, "pages")

    print(f"Total pages fetched: {len(pages)}")

    # Use a progress bar to track the conversion process for posts
    print("Saving posts...")
    for post in tqdm(posts, desc="Converting posts to Markdown", leave=True):
        convert_post_to_md(post, authors, categories, tags, custom_taxonomies, post_type="post")

    # Use a progress bar to track the conversion process for pages
    print("Saving pages...")
    for page in tqdm(pages, desc="Converting pages to Markdown", leave=True):
        convert_post_to_md(page, authors, categories, tags, custom_taxonomies, post_type="page")

def save_authors(domain_url):
    """Fetch and save all authors as markdown metadata."""
    print("Fetching authors...")
    authors = fetch_wordpress_data(domain_url, "users")
    print(f"Total authors fetched: {len(authors)}")

    # Save authors as a YAML metadata file
    authors_path = os.path.join(CONTENT_DIR, "authors.yml")
    authors_dict = {author['id']: author['name'] for author in authors}

    with open(authors_path, "w") as f:
        yaml.dump(authors_dict, f, allow_unicode=True)
    print(f"Saved authors metadata: {authors_path}")

    return authors_dict

def save_categories_and_tags(domain_url):
    """Fetch and save all categories and tags as markdown metadata."""
    print("Fetching categories...")
    categories = fetch_terms_by_taxonomy(domain_url, "categories")
    print(f"Total categories fetched: {len(categories)}")

    print("Fetching tags...")
    try:
        tags = fetch_terms_by_taxonomy(domain_url, "tags")
    except requests.exceptions.JSONDecodeError:
        tqdm.write(f"Tags API did not return valid JSON; continuing without tags.")
        tags = {}

    print(f"Total tags fetched: {len(tags)}")

    # Save categories as a YAML metadata file
    categories_path = os.path.join(CONTENT_DIR, "categories.yml")
    with open(categories_path, "w") as f:
        yaml.dump(categories, f, allow_unicode=True)
    tqdm.write(f"Saved categories metadata: {categories_path}")

    # Save tags as a YAML metadata file
    tags_path = os.path.join(CONTENT_DIR, "tags.yml")
    with open(tags_path, "w") as f:
        yaml.dump(tags, f, allow_unicode=True)
    tqdm.write(f"Saved tags metadata: {tags_path}")

    return categories, tags

if __name__ == "__main__":
    # Use argparse to require domain URL as input
    parser = argparse.ArgumentParser(description="Fetch WordPress data and convert to Markdown")
    parser.add_argument('domain', type=str, help="The WordPress site URL (e.g., https://your-site.com)")

    args = parser.parse_args()
    domain_url = args.domain.rstrip("/")  # Ensure no trailing slash

    # Fetch and save authors, custom taxonomies, posts, pages, categories, and tags
    authors = save_authors(domain_url)
    categories, tags = save_categories_and_tags(domain_url)
    custom_taxonomies = fetch_custom_taxonomies(domain_url)
    save_posts_and_pages(domain_url, authors, categories, tags, custom_taxonomies)
