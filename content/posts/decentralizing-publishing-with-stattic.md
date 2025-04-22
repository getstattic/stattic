---
title: Decentralizing Publishing with Stattic
custom_url: decentralizing-publishing-with-stattic
author: 1
date: 2025-04-22
categories:
  - 0
---

**Stattic** is an open source Python-based static site generator designed to simplify website creation and support the decentralization of publishing, giving the power back into the hands of the creator community where it belongs.

## Key Features of Stattic

The following list is in no particular order and will be changing as Stattic continues to grow with user needs in mind.

### 1. Markdown with Enhanced Features

Stattic uses Markdown for content creation, allowing you to write posts and pages in a straightforward and readable format.

Stattic uses [Mistune](https://mistune.readthedocs.io/en/latest/) with a **custom renderer** that supports:

- Tables
- Task lists
- Strikethrough
- Smart code block rendering with automatic HTML escaping

### 2. Template Rendering with Jinja2

The generator utilizes Jinja2 templates for rendering HTML pages. 

This separation of content and presentation ensures flexibility and ease of maintenance, allowing you to customize the look and feel of your site without altering the content.

### 3. Front Matter Metadata

Each Markdown file can include front matter written in YAML. This metadata lets you define titles, authors, dates, categories, tags, and custom URLs, giving you control over how each page or post is presented.

You can also add any custom metadata you'd like and then use it in the `templates` files, giving you unparalleled control over what content is displayed and in the way you best see fit.

### 4. Automatic Image Handling

Stattic processes images found in your Markdown content by downloading external images, converting them to the efficient WebP format using the Pillow library, and updating the content to reference the local image files. 

This improves site performance and ensures all assets are self-contained right out of the box.

### 5. Google Fonts Integration

The tool can download specified Google Fonts and save them locally. This reduces external dependencies and improves page load times. You can specify fonts like `Quicksand` or `Roboto` directly in the command-line options.

### 6. Asset Management

Stattic handles your CSS and JavaScript assets by copying them from a designated assets directory to the output directory. 

It offers an option to minify these assets using `csscompressor` and `rjsmin`, combining them into single minified files to optimize loading times.

### 7. Logging and Error Handling

Comprehensive logging is also built-in, recording the build process and any issues that arise. Logs are saved in a dedicated `logs` directory, aiding in troubleshooting and ensuring transparency.

### 8. Command-Line Interface

The script includes a command-line interface with options to:

- Specify the output directory.
- Set the number of posts per page.
- Choose sorting preferences (date, title, author).
- Define fonts to download.
- Enable minification of assets.

### 9. Support for Drafts

Posts marked as drafts in their front matter are skipped during the build process, allowing you to work on content without immediately publishing it.

Example: `draft: true`

### 10. Pagination and Sorting

Control how many posts appear on your index page and sort them by date, title, or author. This flexibility helps organize content to suit your audience's needs.

**Example:** `--posts-per-page 5`

### 11. Automatic Excerpts

If an excerpt isn't provided in the front matter, Stattic automatically generates one from the first few words of the content, ensuring that summaries are always available.

**Example:** `excerpt: "Custom text goes here"`

### 12. Customizable Navigation

Pages are loaded and sorted based on an 'order' value in their metadata, allowing you to customize the navigation structure of your site.

In the front matter it's as simple as adding one word and one number.

**Example:** `order: 5`

### 13. RSS Feed and Sitemap Generation

If you provide a `--site-url`, Stattic will:

- Generate a valid RSS 2.0 feed at `/feed/index.xml`
- Output a complete `/sitemap.xml` with last-modified timestamps
- Escape and normalize all URLs and metadata

**Example:** `--site-url https://stattic.site/`

### 14. 404 Page and robots.txt

Stattic builds a default `404.html` using your template and content. You can customize it like any other page.

It also generates a `robots.txt` file based on the mode you choose:

```bash
--robots public   # allow indexing
--robots private  # block all bots
```

If `--site-url` is provided, the `robots.txt` will automatically include a `Sitemap:` line pointing to your `/sitemap.xml`.

## Getting Started with Stattic

1. **Organize Your Content**: Place your Markdown files in the `content/posts` and `content/pages` directories.

2. **Customize Templates**: Modify the templates in the `templates` directory using Jinja2 syntax to match your desired layout and design.

3. **Run the Generator**: Use the command-line interface to build your site:
    
`python3 stattic.py --output ~/my_website --posts-per-page 10 --sort-by date --fonts "Quicksand, Roboto" --minify`

4. **Review the Output**: Your static site will be generated in the specified output directory, ready to be deployed to any static hosting service of your choice.

## Decentralized Publishing for the People

**Stattic** doesn’t ask permission. It gives it back.

No CMS, plugins or middlemen necessary. Just clean, fast publishing on your own terms terms. With full control over your content, your design, and your future.

Whether you're a developer, writer, artist, or creative misfit, Stattic is your toolkit for building an independent web presence without the noise.

It's open source. It's MIT licensed. And it's built to be forked, remixed, and made yours.

Contribute on [GitHub](https://github.com/getstattic/stattic), build something great, and help take the web back — one static site at a time.
