# Stattic - Decentralized Publishing

**Stattic** is a Python-based static site generator that converts Markdown content into static HTML websites using Jinja2 templates. It supports features such as posts, tags, categories, authors, SEO metadata, image optimization, and asset minification, making it ideal for creating fast, lightweight, and SEO-friendly websites.

## Features

- **Markdown-based Content**: Write your content in Markdown files with YAML frontmatter for metadata.
- **Jinja2 Templating**: Customize site layouts using Jinja2 templates located in the `templates/` directory.
- **Pretty Permalinks & Custom URLs**: Generate clean URLs with trailing slashes and set custom URLs via frontmatter.
- **Tags and Categories**: Organize posts with tags and categories, automatically creating archive pages.
- **Authors Support**: Associate posts with authors loaded from `content/authors.yml`.
- **SEO Support**: Add metadata (title, keywords, description) for better SEO.
- **Pagination**: Control the number of posts per page on the homepage.
- **Image Handling**: Automatically download external images, convert them to WebP for optimization, and update URLs in content.
- **Google Fonts Integration**: Download specified Google Fonts and generate corresponding CSS.
- **Asset Management**: Copy and manage CSS, JS, and font assets, with optional minification.
- **RSS Feed and XML Sitemap**: Generate RSS feeds and sitemaps for your site when a site URL is provided.
- **404 Page Generation**: Create a custom `404.html` page for error handling.
- **Logging**: Detailed logs of the build process, including performance metrics and errors.
- **Error Handling**: Gracefully manage template syntax errors, missing files, and download failures.

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Content Organization](#content-organization)
4. [Customization](#customization)
5. [SEO and Metadata](#seo-and-metadata)
6. [Image Optimization](#image-optimization)
7. [Asset Minification](#asset-minification)
8. [RSS Feed and Sitemap](#rss-feed-and-sitemap)
9. [Logging](#logging)
10. [Contributing](#contributing)
11. [License](#license)

---

## Installation

1. **Clone the Repository:**

    ```
    git clone https://github.com/getstattic/stattic.git
    cd stattic
    ```

2. **Install Required Python Dependencies:**

    Ensure you have Python 3.6 or higher installed.

    ```
    pip install -r requirements.txt
    ```

### Requirements

**Python packages (install via pip)**

- `markdown`: Converts Markdown files to HTML.
- `jinja2`: Template engine for rendering HTML pages.
- `pyyaml`: Parses YAML frontmatter from Markdown files.
- `requests`: Downloads external resources like images and fonts.
- `Pillow`: Handles image processing and conversion to WebP.
- `csscompressor`: Minifies CSS files.
- `rjsmin`: Minifies JavaScript files.
- `mistune`: Markdown parser with custom rendering.
- `watchdog`: (Optional) Monitors file changes in watch mode.

**System binaries**

- `gif2webp`: Part of the **libwebp** tools (`brew install webp` or `apt-get install webp`);
              used to convert animated GIFs to animated WebP quickly.
---

## Usage

### **Basic Usage**

To generate the static site, run:

```
python3 stattic.py
```

This command processes the content in the `content/` directory, applies the templates from `templates/`, and outputs the static site to the `output/` directory.

### **Command-Line Arguments**

- `--output`: Specify the output directory. Default is `output`.
    ```
    python3 stattic.py --output ~/Documents/demo
    ```

- `--content`: Specify the content directory. Default is `content`.
    ```
    python3 stattic.py --content ~/Documents/demo-content
    ```

- `--templates`: Specify the templates directory. Default is `templates`.
    ```
    python3 stattic.py --templates ~/Documents/demo-templates
    ```

- `--robots`: Specify if the robots.txt file is public or private. Default is `public`.
    ```
    python3 stattic.py --robots public
    ```

- `--posts-per-page`: Number of posts per index (homepage) page. Default is `5`.
    ```
    python3 stattic.py --posts-per-page 10
    ```

- `--sort-by`: Sort posts by `date`, `title`, `author` or `order`. Default is `date`.
    ```
    python3 stattic.py --sort-by title
    ```

- `--fonts`: Comma-separated list of Google Fonts to download.
    ```
    python3 stattic.py --fonts "Quicksand, Roboto"
    ```

- `--site-url`: Specify the site URL for production builds. Enables RSS feed and sitemap generation.
    ```
    python3 stattic.py --site-url "https://demo.stattic.site"
    ```

- `--minify`: Minify CSS and JS into single files.
    
    ```
    python3 stattic.py --minify
    ```    

- `--watch`: _(Not Implemented)_ Enable watch mode to automatically rebuild on file changes.
    
    ```
    python3 stattic.py --watch
    ```    

**Note:** The `--watch` feature is defined but not yet implemented in the current version of `stattic.py`.

### **Example: Building the Site with Custom Fonts and Minification**
```
python3 stattic.py --output ~/Documents/demo --posts-per-page 10 --sort-by title --fonts "Quicksand, Roboto" --site-url "https://demo.stattic.site" --minify
```

* * *

## Content Organization

### **Directory Structure**

- `content/`
    - `posts/`: Place all blog posts here as Markdown (`.md`) files.
    - `pages/`: Place all static pages (e.g., About, Contact) here as Markdown (`.md`) files.
    - `categories.yml`: Define categories for your posts.
    - `tags.yml`: Define tags for your posts.
    - `authors.yml`: Define authors and their details.
- `templates/`: Contains Jinja2 templates (`base.html`, `post.html`, `index.html`, etc.).
- `assets/`: Contains CSS, JS, and font files to be copied to the `output/assets/` directory.
- `output/`: The generated static site will be placed here.
- `logs/`: Build logs are stored here.

### **Markdown Files with Frontmatter**

Each Markdown file should start with a YAML frontmatter block specifying metadata.

**Example: Blog Post (`content/posts/my-first-post.md`)**

```
---
title: "My First Blog Post"
date: 2024-09-25
tags: [Python, Static Sites]
categories: [Technology]
description: "An introduction to Stattic, a simple static site generator."
custom_url: "my-first-post"
author: 1
draft: false
---

# Welcome to Stattic!

This is my first blog post using **Stattic**.
```

**Example: Static Page (`content/pages/about.md`)**

```
---
title: "About"
custom_url: "about"
description: "Learn more about Stattic and its features."
author: 1
nav_hide: false
---

# About Stattic

Stattic is a Python-based static site generator...
```

* * *

## Customization

### **Templates**

Customize your site's layout by editing Jinja2 templates in the `templates/` directory.

- **`base.html`**: The global layout for all pages. Includes header, footer, and asset links.
- **`post.html`**: Template for individual blog posts.
- **`index.html`**: The main homepage template listing recent posts.
- **`404.html`**: Custom 404 error page.

### **Adding Custom Templates**

You can create additional templates for specific layouts or sections by following the naming conventions and extending `base.html`.

* * *

## SEO and Metadata

Enhance your site's SEO by adding metadata in the frontmatter of your Markdown files.

- **`title`**: The title of the page or post.
- **`description`**: A brief description for SEO purposes.
- **`keywords`**: Relevant keywords for the page or post.
- **`author`**: The author ID as defined in `authors.yml`.
- **`custom_url`**: Custom URL slug for the page or post.
- **`canonical`**: The canonical URL for the page or post.

**Example:**

```
---
title: "SEO Optimization with Stattic"
description: "Learn how to optimize your static site for search engines."
keywords: [SEO, Static Site, Optimization]
custom_url: "seo-optimization"
canonical: "https://yourdomain.com/custom-url"
author: 2
---
```

* * *

## Image Optimization

Stattic automatically handles image optimization by:

1. **Downloading External Images**: Images referenced via URLs in your content are downloaded and stored locally in the `output/images/` directory.
2. **Converting to WebP**: Downloaded images are converted to WebP format for better performance.
3. **Updating Image URLs**: Image references in your content are updated to point to the optimized WebP versions.

**Example:**

```    
![Logo](https://example.com/images/logo.png)
```

After processing, the above will be converted to:

```
<img src="images/logo.webp" alt="Logo">
```

* * *

## Asset Minification

Improve your site's performance by minifying CSS and JavaScript assets.

- **Enable Minification**: Use the `--minify` flag when running `stattic.py`.

```
python3 stattic.py --minify
```

- **Minified Files**:

    - `output/assets/css/main.min.css`: Combined and minified CSS.
    - `output/assets/js/main.min.js`: Combined and minified JavaScript.

**Note:** Ensure that your templates reference these minified files when the `--minify` flag is used.
* * *

## RSS Feed and Sitemap

Generate an RSS feed and XML sitemap for your site by providing the `--site-url` argument.

- **Generate RSS Feed and Sitemap**:
    ```
    python3 stattic.py --site-url "https://demo.stattic.site"
    ```

- **Generated Files**:

    - `output/feed/index.xml`: RSS feed containing your latest posts.
    - `output/sitemap.xml`: XML sitemap listing all pages and posts.

**Note:** RSS and sitemap generation are only enabled when a valid `--site-url` is provided.
* * *

## Logging

Stattic provides detailed logs of the build process, including performance metrics and errors.

- **Log Files**: Stored in the `logs/` directory with timestamps.

**Example Log Entry:**

```
2024-09-27 12:34:56 - INFO - Starting build process...
2024-09-27 12:34:56 - INFO - Created output directory: output
2024-09-27 12:34:57 - INFO - Loaded 3 categories and 5 tags
2024-09-27 12:34:57 - INFO - Converted Markdown to HTML using Mistune (Time taken: 0.45 seconds)
2024-09-27 12:34:58 - INFO - Generated post: output/blog/my-first-post/index.html
2024-09-27 12:34:59 - INFO - Generated index page: output/index.html
2024-09-27 12:34:59 - INFO - Site build completed successfully in 3.00 seconds.
```

- **Console Output**: Also displays INFO level logs for real-time feedback.
* * *

## Contributing

We welcome contributions! To contribute:

1. **Fork the Repository:**

```
git clone https://github.com/getstattic/stattic.git
cd stattic
```

2. **Create a New Branch:**

```
git checkout -b feature-branch
```

3. **Make Your Changes**: Implement your features or fixes.

4. **Commit Your Changes:**

```
git commit -m "Add feature XYZ"
```

5. **Push to Your Fork:**

```
git push origin feature-branch
```

6. **Submit a Pull Request**: Open a pull request detailing your changes.

* * *

## License

This project is licensed under the MIT License. See the [LICENSE](/LICENSE) file for details.

* * *

## Additional Notes (01/06/2025)

1. **Watch Mode Implementation:**

    - Currently, the `--watch` flag is defined but not implemented. Future updates will include automatic rebuilding when content or templates change.
2. **Directory Structure Consistency:**

    - Maintain a consistent directory structure to ensure relative paths are correctly calculated and assets are properly linked.
3. **Error Handling:**

    - Review the logs in the `logs/` directory if you encounter any issues during the build process.
4. **Extending Features:**

    - Consider adding features like search functionality, custom taxonomies, or integration with third-party services as needed.