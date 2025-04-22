---
title: How to Build and Deploy Your Website with Stattic and GitHub Pages
custom_url: build-with-stattic-and-deploy-on-github-pages
author: 1
date: 2025-04-22
categories:
  - 5
  - 6
  - 7
---

With Stattic, you can easily build a static site and deploy it to [GitHub Pages](https://pages.github.com/) for free hosting. This guide will walk you through how to create your site, export the build files to a GitHub repository, and automate your workflow to push updates live.

## Prerequisites

Before we start, make sure you have the following:

-   **GitHub Account**: [Sign up](https://github.com/) if you don't have one.
-   **Git Installed**: You can download and install Git from [here](https://git-scm.com/downloads).
-   **Stattic Installed**: Make sure you have Stattic set up on your machine. If not, follow the installation instructions.

* * * * *

## Step 1: Build Your Site with Stattic

First, generate your site's content using Stattic.

1.  **Create Your Site Content**

    -   Add Markdown files to the `content/posts/` folder for blog posts.
    -   Add Markdown files to the `content/pages/` folder for static pages like About or Contact.
2.  **Customize Your Site**

    -   Modify the templates in the `templates/` folder for custom layouts.
    -   Customize your styles in `assets/css/stattic.css`.
3.  **Run the Build Command**

    In your terminal, navigate to your project folder and run:

    ```yaml
    python3 stattic.py --output ./build --fonts "Quicksand"
    ```

    This command generates the static files in the `./build` directory. You can also pass a font list with the `--fonts`option to use fonts from Google Fonts. If you don't specify a font, it defaults to Quicksand.

    If you're rebuilding, it's a good idea to clear the output directory first:

    ```yaml
    rm -rf build && mkdir build
    ```

* * * * *

## Step 2: Set Up a GitHub Repository

1.  **Create a New GitHub Repository**

    - Go to [GitHub](https://github.com/) and create a new repository. Name it `your-username.github.io` if you want to use [GitHub Pages](https://pages.github.com/) (replace `your-username` with your actual GitHub username).
    - If you want your site at `https://your-username.github.io/`, name the repo `your-username.github.io`.
    - For project pages (e.g. `your-username.github.io/your-repo-name/`), you can name it anything.

2.  **Clone the Repository Locally** - Open your terminal, navigate to the directory where you want to clone your repository, and run:

    `git clone https://github.com/your-username/your-repo-name.git`

    Replace `your-username/your-repo-name` with your GitHub username and repository name.

* * * * *

## Step 3: Copy Your Build Files to the Repo

1.  **Move Your Build Files** - After running the build command, copy the contents of the `./build` directory into your GitHub repository:

    `cp -r build/* your-repo-name/`

2.  **Navigate to the Repository Folder** - Navigate into your repository directory:

    `cd your-repo-name`

* * * * *

## Step 4: Push Your Site to GitHub Pages

1.  **Stage and Commit the Files** - Add the files to your Git repository:

    `git add .`

    Then commit them:

    `git commit -m "Initial commit for static site"`

2.  **Push to GitHub** - Push the changes to your GitHub repository:

    `git push origin main`

* * * * *

## Step 5: Enable GitHub Pages

1. **Configure GitHub Pages** - Go to your GitHub repository, click the **Settings** tab, then scroll to the **Pages** section.
    - If you're deploying the build output to the root of your repo, select:
        - **Branch**: `main`
        - **Folder**: `/ (root)`
    - If you prefer to keep your source files and deploy only the build output:
        - Move the contents of `build/` into a `/docs` folder inside the repo.
        - Then select:
            - **Branch**: `main`
            - **Folder**: `/docs`
    Click **Save** when you're done.
2.  **Access Your Site** - After a few minutes, your site will be live at `https://your-username.github.io/`.

* * * * *

## Step 6: Automate Future Builds

Whenever you update your content, rebuilding and deploying the site is quick and easy.

1.  **Rebuild Your Site** - After adding new posts or making changes, run the build command again:

    `python3 stattic.py --output ./build --fonts "Quicksand"`

2.  **Copy and Push the New Build** - Copy the updated files to your GitHub repository:

    `cp -r build/* your-repo-name/`

    Navigate to the repository:

    `cd your-repo-name`

    Then, add, commit, and push the changes:

    ```
    git add .
    git commit -m "Updated content"
    git push origin main
    ```

3.  **GitHub Pages Auto-Update** - GitHub Pages will automatically rebuild your site, and your updates will go live.

* * * * *

Using Stattic with [GitHub Pages](https://pages.github.com/) is a fast and efficient way to manage and host static websites. You can:

-   Generate optimized static files with Stattic.
-   Use GitHub Pages for free, easy hosting.
-   Automate your updates with Git's simple push commands.

With no databases and minimal setup, you can enjoy a streamlined and secure static site. It's fast, secure, and lightweight---perfect for blogging, portfolios, documentation, and more.

* * * * *

### **Happy Building with Stattic!**