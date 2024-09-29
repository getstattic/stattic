# Stattic - A Simple Static Site Generator

**Stattic** is a Python-based static site generator designed to convert Markdown content into static HTML websites using Jinja2 templates. It supports features such as posts, tags, categories, SEO metadata, and watch mode for dynamic content generation.

## Features

- **Markdown-based content**: Write your content in Markdown files.
- **Jinja2 templating**: Customize site layouts with Jinja2 templates.
- **Pretty permalinks**: Clean URLs generated automatically.
- **Custom URLs**: Set custom slugs for posts via frontmatter metadata.
- **Tags and Categories**: Automatically creates tag and category archive pages.
- **SEO support**: Add metadata (title, keywords, description) for better SEO.
- **Watch mode**: Automatically rebuilds the site upon file changes.
- **Pagination**: Supports pagination for posts, tag, and category views.
- **Image handling**: Automatic image downloading and embedding.
- **Logging**: Detailed logs of the build process.
- **Error handling**: Manages template syntax and file handling errors gracefully.

---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Content Organization](#content-organization)
4. [Customization](#customization)
5. [Watch Mode](#watch-mode)
6. [Logging](#logging)
7. [Contributing](#contributing)
8. [License](#license)

---

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/getstattic/stattic.git
    cd stattic
    ```

2. Install required Python dependencies:

    ```
    pip install -r requirements.txt
    ```

### Requirements

- `markdown`: Converts Markdown files to HTML.
- `jinja2`: Template engine for rendering HTML pages.
- `pyyaml`: Parses YAML frontmatter from Markdown files.
- `watchdog`: Monitors file changes in watch mode (optional).
- `PIL`: Handles image downloads and processing.
- `requests`: For downloading external images.

---

## Usage

1. Place Markdown content in the `content/` directory. Posts go in `content/posts/`, and static pages (like "About" or "Contact") go in `content/pages/`.

2. To generate the static site, run:

    ```
    python stattic.py
    ```

3. The generated HTML files will be in the `output/` directory.

4. To enable watch mode (rebuild on file change), use:

    ```
    python stattic.py --watch
    ```

---

## Content Organization

- **Markdown Files**: All posts and pages should be written in Markdown.
- **Frontmatter**: Each Markdown file should start with a YAML frontmatter block, specifying the metadata (title, date, tags, custom URL, etc.).
- **Images**: Stattic can download and embed images in your posts automatically. Ensure that you specify the URLs properly in your content.

### Example Markdown Post with Frontmatter

```
---
title: "My First Blog Post"
date: 2024-09-25
tags: [Python, Static Sites]
description: "A brief introduction to Stattic"
custom_url: "my-first-post"
---

# Welcome to Stattic!

This is my first blog post using **Stattic**.
```

---

## Customization

### Templates
Stattic uses Jinja2 templates, located in the `templates/` directory, to render your site's layout. You can customize the following templates:

* `base.html`: The global layout for the site.
* `post.html`: Template for individual posts.
* `index.html`: The main homepage.
* `category.html`: Template for category pages.

### Custom URLs
Set custom URLs for posts in the frontmatter using the `custom_url` key.

---

## Watch Mode

When developing, Stattic offers a watch mode that automatically rebuilds the site when it detects changes in your content or templates.

```
python stattic.py --watch
```

---

## Logging

Stattic generates detailed logs of the build process, including performance metrics and errors. Logs are saved in the logs/ directory.

### Example of log output:

```
2024-09-27 12:34:56 - INFO - Starting build process...
2024-09-27 12:34:56 - INFO - Created output directory: output
2024-09-27 12:34:57 - INFO - Parsed 3 Markdown files in content
2024-09-27 12:34:57 - INFO - Build completed successfully in 1.5 seconds.
```

---

## Contributing

We welcome contributions! To contribute:

* Fork this repository.
* Create a new branch (`git checkout -b feature-branch`).
* Make your changes.
* Submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](/LICENSE) file for details.