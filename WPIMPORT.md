# WordPress Content Importer (wpImport.py)

The `wpImport.py` script is a utility for migrating content from a WordPress site to a static site generator by fetching data via the WordPress REST API and converting it to Markdown format. The script downloads posts, pages, categories, tags, authors, and custom taxonomies and saves them in a structured Markdown format, along with YAML frontmatter metadata.

## Features

- **Fetch WordPress content**: Retrieve posts, pages, categories, tags, and custom taxonomies.
- **HTML to Markdown conversion**: Converts WordPress HTML content into Markdown.
- **YAML frontmatter**: Automatically adds metadata such as title, author, date, categories, and tags.
- **Support for custom taxonomies**: Fetches and integrates custom taxonomies defined in WordPress.
- **Progress bars**: Displays progress using `tqdm` for long-running operations.
- **Error handling**: Gracefully handles HTTP, JSON, and other errors during content retrieval.

---

## Prerequisites

- Python 3.x
- Required Python libraries:
  - `requests`
  - `html2text`
  - `pyyaml`
  - `tqdm`

These are already in the requirements.txt file you installed from the README.md file. If you are running this script separately in a different location, you can install the necessary dependencies with:

```
install requests html2text pyyaml tqdm
```

---

## Usage

### 1. Fetch and Convert WordPress Data

To run the script, you need to provide the base URL of your WordPress site (make sure the WordPress REST API is enabled). The script will automatically download and convert posts, pages, categories, tags, and authors into Markdown.

```
python3 wpImport.py https://your-wordpress-site.com
```

This command will:

* Fetch and save authors in a YAML file.
* Fetch and convert posts and pages into Markdown files with YAML frontmatter.
* Fetch categories and tags, saving them in separate YAML files.
* Download custom taxonomies if any are available and integrate them into the Markdown content.

### 2. Files Generated

The script saves the downloaded content in a directory called `content/`:

**Markdown files:**

* Posts are saved in `content/posts/`
* Pages are saved in `content/pages/`

**Metadata:**

`content/authors.yml`: Contains author information.
`content/categories.yml`: Contains category data.
`content/tags.yml`: Contains tag data.

### Example YAML Frontmatter in Markdown

Each post or page is saved as a Markdown file with the following YAML frontmatter:

```
---
title: "Sample Blog Post"
date: 2024-09-25
author: "John Doe"
categories:
  - "Python"
tags:
  - "Migration"
excerpt: "This is a sample blog post."
custom_url: "sample-blog-post"
---
```

The body of the content is in Markdown format.

---

## Error Handling

The script handles common errors that may occur during the WordPress data retrieval process:

* **HTTP Errors**: If the REST API endpoint is unreachable or returns an invalid status, the error is logged and the script continues.
* **JSON Decoding Errors**: If the response is not valid JSON, the script will log the error and proceed with the next item.
* **Progress Bars**: For large datasets, progress bars will indicate the status of the data fetching and conversion.