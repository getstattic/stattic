---
title: "Customizing Stattic: Front Matter Fields"
custom_url: front-matter-fields-for-stattic
author: 1
date: 2024-09-30
categories:
  - 1
---

### 1. **title**

- **Description**: The title of your post or page.
- **Type**: String
- **Default**: `'Untitled'`
- **Usage**:

    `title: "Your Post Title"`

### 2. **date**

- **Description**: The publication date of your post or page.
- **Type**: String (formatted as `YYYY-MM-DDTHH:MM:SS`)
- **Default**: Current date and time if not provided.
- **Usage**:

    `date: "2023-10-15T10:00:00"`

### 3. **author**

- **Description**: The ID of the author of the post or page.
- **Type**: Integer or String (should correspond to an ID in `authors.yml`)
- **Default**: `'Unknown'` if not provided.
- **Usage**:

    `author: 1  # Assuming '1' corresponds to an author in authors.yml`

### 4. **categories**

- **Description**: A list of category IDs that the post belongs to.
- **Type**: List of Integers (IDs corresponding to entries in `categories.yml`)
- **Default**: Empty list `[]` if not provided.
- **Usage**:

```
    categories:
      - 2
      - 5
 ```

### 5. **tags**

- **Description**: A list of tag IDs associated with the post.
- **Type**: List of Integers (IDs corresponding to entries in `tags.yml`)
- **Default**: Empty list `[]` if not provided.
- **Usage**:

```
    tags:
      - 3
      - 7
```

### 6. **draft**

- **Description**: Indicates whether the post is a draft.
- **Type**: Boolean (`true` or `false`)
- **Default**: `false` (the post will be published by default)
- **Usage**:

    `draft: true  # The post will be skipped during the build process`

### 7. **template**

- **Description**: Specifies a custom template to use for rendering.
- **Type**: String (the name of the template part)
- **Default**: `'post.html'` for posts, `'page.html'` for pages if not specified.
- **Usage**:

    `template: "custom"  # Will use 'post-custom.html' or 'page-custom.html'`

### 8. **custom_url**

- **Description**: Custom URL slug for the post or page.
- **Type**: String
- **Default**: The filename without the `.md` extension.
- **Usage**:

    `custom_url: "my-custom-path"`

### 9. **order**

- **Description**: Determines the order of pages in navigation menus.
- **Type**: Integer (lower numbers appear first)
- **Default**: `100` if not specified.
- **Usage**:

    `order: 1  # This page will appear before pages with higher 'order' values`

### 10. **featured_image**

- **Description**: URL of the featured image for the post or page.
- **Type**: String (URL)
- **Default**: `None` if not provided.
- **Usage**:

    `featured_image: "https://example.com/images/featured.jpg"`

### 11. **seo_title**

- **Description**: Custom title for SEO purposes.
- **Type**: String
- **Default**: Uses the `title` field if not provided.
- **Usage**:

    `seo_title: "Optimized SEO Title for Search Engines"`

### 12. **keywords**

- **Description**: SEO keywords for the post or page.
- **Type**: String (comma-separated)
- **Default**: Empty string `''` if not provided.
- **Usage**:

    `keywords: "keyword1, keyword2, keyword3"`

### 13. **description**

- **Description**: SEO description for the post or page.
- **Type**: String
- **Default**: Empty string `''` if not provided.
- **Usage**:

    `description: "A brief description of the content for SEO purposes."`

### 14. **lang**

- **Description**: Language code for the content.
- **Type**: String (e.g., `'en'`, `'fr'`, `'es'`)
- **Default**: `'en'` (English) if not specified.
- **Usage**:

    `lang: "en"`

### 15. **excerpt**

- **Description**: Custom excerpt or summary of the post.
- **Type**: String (supports Markdown)
- **Default**: Automatically generated from the first 30 words of the content if not provided.
- **Usage**:

    `excerpt: "This is a custom excerpt for the post."`

* * *

## Additional Details and Usage

### **Categories and Tags**

- **Definition Files**: Categories and tags are defined in `categories.yml` and `tags.yml`, respectively.
- **Structure of YAML Files**:
```
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

```
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
```
    # authors.yml
    1: "Jane Doe"
    2: "John Smith"
```

- **Usage in Front Matter**:

    `author: 1  # Refers to "Jane Doe"`

### **Custom Templates**

- **Templates Directory**: Templates are stored in the `templates` directory.
- **Template Naming**:
    - For posts: `post.html` or `post-{template}.html`
    - For pages: `page.html` or `page-{template}.html`
- **Usage**:

    `template: "gallery"  # Will use 'post-gallery.html' or 'page-gallery.html'`
 
### **Example of Complete Front Matter**

```
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

- **Front Matter Format**: Ensure the front matter is enclosed at the top of your Markdown file between `---` lines.
- **YAML Syntax**: Use proper YAML syntax to avoid parsing errors. Indentation and formatting are important.
- **Optional Fields**: All fields are optional unless required by your site's design or functionality. The script provides default values where appropriate.
- **Draft Posts**:
    - Set `draft: true` to exclude a post from the build.
    - Remove the `draft` field or set it to `false` when you're ready to publish.
- **Custom URLs**:
    - Use `custom_url` to define a specific path for your post or page.
    - If not specified, the filename (without the `.md` extension) is used as the slug.

* * *

## Summary

By utilizing these front matter fields, you can control various aspects of how your content is processed and displayed by the **Stattic** static site generator. 

This includes metadata for SEO, content organization through categories and tags, custom templates for different types of content, and more.

Feel free to include any or all of these fields in the front matter of your Markdown files to customize your site's behavior and appearance according to your needs.