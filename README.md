# Stattic - A Simple Static Site Generator

Stattic is a simple yet powerful static site generator written in Python. It takes content written in Markdown and uses Jinja2 templates to generate static HTML pages. The generator supports blog posts, tag and category pages, static pages (like About or Contact), custom URLs, SEO metadata, and more.

## Features

- **Markdown-based**: Write your content in Markdown files.
- **Jinja2 templating**: Customize the look and feel of your site using Jinja2 templates.
- **Pretty permalinks**: Automatically generates pretty permalinks for posts and pages.
- **Custom URLs**: Supports custom slugs for posts via `custom_url` metadata.
- **Tags and Categories**: Automatically generates tag and category pages.
- **SEO support**: Include metadata for SEO such as `title`, `keywords`, and `description`.
- **Watch mode**: Automatically rebuilds the site when changes are detected.
- **Logging**: Detailed logging of the build process, including performance metrics.
- **Pagination**: Configurable number of posts per page for index, tag, and category pages.

---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Markdown Structure](#markdown-structure)
4. [Templates](#templates)
5. [Customizing Your Site](#customizing-your-site)
6. [Watch Mode](#watch-mode)
7. [Logging](#logging)
8. [Contributing](#contributing)
9. [License](#license)

---

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/yourusername/stattic.git
    cd stattic
    ```

2. Install the required Python dependencies:

    ```
    pip install -r requirements.txt

    ```

The dependencies include:

* `markdown`: Converts Markdown content to HTML.
* `jinja2`: Templating engine for rendering HTML.
* `pyyaml`: Parses YAML frontmatter from Markdown files.
* `watchdog`: Optional for monitoring file changes in watch mode.

---

## Usage

1. Write your content in Markdown and save it in the content/ directory. Each Markdown file can contain metadata in YAML frontmatter.

2. Run the generator to generate the static HTML files:

    ```
    python stattic.py --output my-site --posts-per-page 5 --sort-by date
    ```

    This will generate your site in the my-site/ directory, with pagination for index pages.

3. Visit the generated HTML files in your browser by opening them from the my-site/ directory.

---

## Markdown Structure

Each Markdown file in the content/ directory should follow this structure:

```
---
title: "Your Post Title"
author: "Author Name"
date: "2024-09-27"
categories: ["Category1", "Category2"]
tags: ["tag1", "tag2"]
featured_image: "/path/to/featured_image.jpg"
seo_title: "Custom SEO Title"
keywords: "keyword1, keyword2"
description: "Custom meta description for SEO."
custom_url: "your-custom-slug" # Optional custom URL
draft: false
excerpt: "This is a custom excerpt for the post."
---
# Your Post Content in Markdown

Here is the main content of your post, written in Markdown.
```

### Frontmatter Fields

* title: Title of the post.
* author: The author of the post.
* date: The date of the post (format: YYYY-MM-DD).
* categories: A list of categories for the post.
* tags: A list of tags for the post.
* featured_image: URL for the featured image of the post.
* seo_title: Custom title for SEO (optional).
* keywords: SEO keywords (comma-separated).
* description: Meta description for SEO.
* custom_url: Optional custom URL slug for the post (e.g., my-custom-slug).
* draft: Set to true to mark a post as a draft and skip generation.
* excerpt: Optional custom excerpt for the post.

---

## Templates

You can fully customize the look and feel of your site using Jinja2 templates. Templates should be placed in the templates/ directory.

### Example Template Files

* base.html: The base layout for your site, including the header, footer, and main structure.
* post.html: Template for rendering individual blog posts.
* index.html: Template for the homepage, showing a list of blog posts.
* tag.html: Template for displaying posts under a specific tag.
* category.html: Template for displaying posts in a specific category.
* page.html: Template for static pages like "About" or "Contact".

### Example `base.html`

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | My Blog</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <h1>My Blog</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/about.html">About</a>
        </nav>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>© 2024 My Static Site</p>
    </footer>
</body>
</html>
```

---

## Customizing Your Site

* **Modify templates:** You can update the HTML structure or styling by editing the templates in the `templates/` directory.
* **Add static pages:** Create static pages like about.md or contact.md in the `content/` directory, and they will be generated into HTML.
* **Use custom URLs:** Define a `custom_url` in the frontmatter to customize the URL slug of a post.

---

## Watch mode

To have the generator automatically rebuild the site when you make changes to files, use the `--watch` flag:

```
python stattic.py --output my-site --watch
```

In this mode, the site will be regenerated every time a file in the `content/` or `templates/` directory changes.

---

## Logging

All build activity, including errors, warnings, and performance metrics, are logged to `stattic.log`.

Logs build duration: Shows how long it takes to build the site.

Logs generated pages/posts: Displays the total number of posts and pages generated during the build.

### Example of log output (`stattic.log`):

```
2024-09-27 12:34:56,789 - INFO - Starting build process...
2024-09-27 12:34:56,790 - INFO - Created output directory: output
2024-09-27 12:34:56,801 - INFO - Found 3 markdown files in content (Time taken: 0.12 seconds)
2024-09-27 12:34:57,001 - INFO - Parsed markdown file: content/post-1.md (Time taken: 0.20 seconds)
2024-09-27 12:34:57,200 - INFO - Generated post: output/en/posts/post-1/index.html
2024-09-27 12:34:57,205 - INFO - Site build completed successfully in 1.50 seconds.
2024-09-27 12:34:57,210 - INFO - Total posts generated: 3
2024-09-27 12:34:57,211 - INFO - Total pages generated: 2
```

---

## Contributing

We welcome contributions! To get started:

* Fork this repository.
* Create a new branch (`git checkout -b feature-branch`).
* Make your changes.
* Submit a pull request.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.