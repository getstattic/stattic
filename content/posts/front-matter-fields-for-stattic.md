---
title: "Customizing Stattic: Front Matter Fields"
custom_url: front-matter-fields-for-stattic
author: 1
date: 2025-04-22
categories:
  - 1
---

Below is a comprehensive list of all of the front matter fields that are used by Stattic.

### 1. title

- **Description**: The title of your post or page.
- **Type**: String
- **Default**: `'Untitled'`
- **Usage**:

```yaml
title: "Your Post Title"`
```

### 2. date

- **Description**: The publication date of your post or page.
- **Type**: String  
  *(Accepted formats include `YYYY-MM-DDTHH:MM:SS`, `YYYY-MM-DD`, or `Mon DD, YYYY` (e.g., "Oct 15, 2023"))*
- **Default**: Current date and time if not provided.
- **Usage**:

```yaml
date: "2023-10-15T10:00:00"
```

### 3. author

- **Description**: The ID of the author of the post or page.
- **Type**: Integer or String – should correspond to an ID in `authors.yml`.  
  **Note:** For proper sorting by author, ensure the author field is nested under `metadata` if your system requires it.
- **Default**: `'Unknown'` if not provided.
- **Usage**:

```yaml
metadata:
    author: 1  # Corresponds to an author defined in authors.yml
```

### 4. categories

- **Description**: A list of category IDs that the post belongs to.
- **Type**: List of Integers (IDs corresponding to entries in `categories.yml`)
- **Default**: Empty list `[]` if not provided.
- **Usage**:

```yaml
categories:
    - 2
    - 5
```

### 5. tags

- **Description**: A list of tag IDs associated with the post.
- **Type**: List of Integers (IDs corresponding to entries in `tags.yml`)
- **Default**: Empty list `[]` if not provided.
- **Usage**:

```yaml
tags:
    - 3
    - 7
```

### 6. draft

- **Description**: Indicates whether the post is a draft.
- **Type**: Boolean (`true` or `false`)
- **Default**: `false` (the post will be published by default)
- **Usage**:

```yaml
draft: true  # The post will be skipped during the build process
```

### 7. template

- **Description**: Specifies a custom template to use for rendering.
- **Type**: String (the name of the template part)
- **Default**: `'post.html'` for posts, `'page.html'` for pages if not specified.
- **Usage**:

```yaml
template: "custom"  # Will use 'post-custom.html' or 'page-custom.html'
```

### 8. custom_url

- **Description**: Custom URL slug for the post or page.
- **Type**: String
- **Default**: The filename without the `.md` extension.
- **Usage**:

```yaml
custom_url: "my-custom-path"
```

### 9. order

- **Description**: Intended to determine the order of pages in navigation menus.  
  **Note:** Currently, post sorting is based on the `--sort-by` option (date, title, or author). The `order` field is available for use by custom templates or additional logic.
- **Type**: Integer (lower numbers appear first)
- **Default**: `100` if not specified.
- **Usage**:

```yaml
order: 1  # Used by custom logic for navigation ordering
```

### 10. featured_image

- **Description**: URL of the featured image for the post or page.
- **Type**: String (URL)
- **Default**: `None` if not provided.
- **Usage**:

```yaml
featured_image: "https://example.com/images/featured.jpg"
```

### 11. seo_title

- **Description**: Custom title for SEO purposes.
- **Type**: String
- **Default**: Uses the `title` field if not provided.
- **Usage**:

```yaml
seo_title: "Optimized SEO Title for Search Engines"
```

### 12. keywords

- **Description**: SEO keywords for the post or page.
- **Type**: String (comma-separated)
- **Default**: Empty string `''` if not provided.
- **Usage**:

```yaml
keywords: "keyword1, keyword2, keyword3"
```

### 13. description

- **Description**: SEO description for the post or page.
- **Type**: String
- **Default**: Empty string `''` if not provided.
- **Usage**:

```yaml
description: "A brief description of the content for SEO purposes."
```

### 14. lang

- **Description**: Language code for the content.
- **Type**: String (e.g., `'en'`, `'fr'`, `'es'`)
- **Default**: `'en'` (English) if not specified.
- **Usage**:

```yaml
lang: "en"
```

### 15. excerpt

- **Description**: Custom excerpt or summary of the post. Supports Markdown.  
  **Note:** If not provided, an excerpt is automatically generated (typically from the first 30 words) unless overridden.
- **Type**: String
- **Default**: Automatically generated from the content or defaults to `"No description available"` in RSS feeds.
- **Usage**:

```yaml
excerpt: "This is a custom excerpt for the post."
```

### 16. permalink

- **Description**: The URL slug for the post or page, used to generate absolute URLs for feeds and sitemaps.
- **Type**: String
- **Default**: Derived from `custom_url` if provided, or from the filename (without the `.md` extension).
- **Usage**:

```yaml
permalink: "exploring-the-stars"
```

## Additional Details and Usage

### **Categories and Tags**

- **Definition Files**: Categories and tags are defined in `categories.yml` and `tags.yml`, respectively.
- **Structure of YAML Files**:
```yaml
# categories.yml
1:
    name: "Technology"
2:
    name: "Science"

# tags.yml
1:
    name: "Python"
2:
    name: "AI"
```
- **Usage in Front Matter**:

```yaml
categories:
    - 1  # Refers to "Technology"
    - 2  # Refers to "Science"
tags:
    - 1  # Refers to "Python"
    - 2  # Refers to "AI"
```

### **Authors**

- **Definition File**: Authors are defined in `authors.yml`.
- **Structure**:
```yaml
# authors.yml
1: "Jane Doe"
2: "John Smith"
```

- **Usage in Front Matter**:

```yaml
author: 1  # Refers to "Jane Doe"
```

### **Custom Templates**

- **Templates Directory**: Templates are stored in the `templates` directory.
- **Template Naming**:
    - For posts: `post.html` or `post-{template}.html`
    - For pages: `page.html` or `page-{template}.html`
- **Usage**:

```yaml
template: "gallery"  # Will use 'post-gallery.html' or 'page-gallery.html'
```
 
### **Example of Complete Front Matter**

```yaml
---
title: "Exploring the Stars"
date: "2023-10-15T10:00:00"
author: 2
categories:
    - 3
    - 4
tags:
    - 5
    - 6
draft: false
template: "astronomy"
custom_url: "exploring-the-stars"
order: 2
featured_image: "https://example.com/images/stars.jpg"
seo_title: "A Deep Dive into Astronomy"
keywords: "astronomy, stars, space"
description: "An in-depth exploration of the wonders of the universe."
lang: "en"
excerpt: "Join us as we journey through the cosmos, exploring the mysteries of the stars..."
---
```

* * *

## Notes on Usage

- **Front Matter Format**: Always place your front matter at the top of your Markdown file, enclosed between `---` lines.  
Example:
    
```yaml
---
title: "My Post Title"
date: "2024-04-22"
---
```

- **YAML Syntax**: Use proper YAML formatting. Watch for:
    - Correct indentation (2 spaces is standard)
    - No tab characters
    - String values with special characters (like `:`) should be quoted
- **Optional Fields**: All fields are optional unless required by your site's design or templates.  
Default values are applied automatically if a field is missing.
- **Date Formats**: Dates can be written in any of the following formats:
    - `YYYY-MM-DDTHH:MM:SS` (recommended)
    - `YYYY-MM-DD`
    - `Apr 22, 2025`  
If the date is invalid or missing, a default fallback will be used (e.g., the current date or minimum sort date).
- **Draft Posts**:
    - Use `draft: true` to prevent a post from being built.
    - When ready to publish, set `draft: false` or remove the line entirely.
- **Custom URLs**:
    - Use `custom_url` to control the output slug and permalink.
    - If omitted, the filename (without `.md`) will be used as the URL.
    - Internally, this field maps to `permalink` in feeds and sitemaps.
- **Excerpt Behavior**:
    - If `excerpt` is provided in the front matter, it will be used.
    - If omitted, an automatic excerpt is generated from the first 30 words of the post.
- **Image Handling**:
    - Local and remote images used in content or `featured_image` are downloaded and converted to WebP.
    - All image references (`src`, `href`, `srcset`, and Markdown syntax) are automatically updated.

## Summary

By defining values in your Markdown file's front matter, you gain fine-grained control over how content is handled, presented, and optimized by **Stattic**.

Whether you're managing SEO, structuring navigation, hiding drafts, or linking to custom permalinks, front matter fields let you customize:

- Meta details like `seo_title`, `keywords`, `description`
- Layout via `template`
- Content organization using `categories` and `tags`
- Author attribution with `author`
- Media presentation with `featured_image` and automatic excerpting

You can include as few or as many of these fields as needed. Stattic will fill in any gaps with sensible defaults--so your content builds fast, clean, and reliably.