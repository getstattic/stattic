# CHANGELOG.md

## 0.3.0

* [📦 NEW: Added generator for llms.txt file](https://github.com/getstattic/stattic/commit/1d54f3c7ff724eb3467979c30bd9de5b1621b8cf)
* [👌 IMPROVE: Removed 9 unnecessary methods from the Stattic class](https://github.com/getstattic/stattic/commit/e29d68e6aba28731fd50372e67b69548508d639b)
* [👌 IMPROVE: Updated animated GIF handling speed by converting via gif2webp with Pillow fallback](https://github.com/getstattic/stattic/commit/6411fba18d095c0ddc9ec3ac2c73f860dfcf7555)
* [👌 IMPROVE: Updated sort-by to include 'order' which works with the front matter](https://github.com/getstattic/stattic/commit/6493127733ba43caec35d9c55efd05e9e3ef55ea)
* [👌 IMPROVE: Skip default index.html if custom home page is detected; add redirect for missing blog page](https://github.com/getstattic/stattic/commit/728953f5880d9be927ffb54b7cb89be87feffc70)
* [👌 IMPROVE: Updated /blog/ to redirect to the home page if no custom home or blog templates are included](https://github.com/getstattic/stattic/commit/b968110157e534585e9f88261bcf043f77c41ef6)
* [👌 IMPROVE: Updated broken link in the demo contact page content](https://github.com/getstattic/stattic/commit/a4db559fab0fbbeba142f61754f929512081b8e7)
* [👌 IMPROVE: Updated render_template to always include site_url and optionally override relative_path if site_url is set](https://github.com/getstattic/stattic/commit/8c9c45fadb93de0246845b051626b1a350903c57)
* [👌 IMPROVE: General code cleanup](https://github.com/getstattic/stattic/commit/d85c58b874184af6f5a6ebf98a186e95874ed14a)
* [📖 DOC: Aded gif2webp to the Requirements section](https://github.com/getstattic/stattic/commit/4c04cde7103afe15196dddff02345129f367638d)
* [📖 DOC: Updated README with a couple quick fixes](https://github.com/getstattic/stattic/commit/696a37cab6161c0178bfc0e0070d51f523d9f219)

## 0.2.0

- [🐛 BUG: Fixed Markdown tables rendering as raw HTML](https://github.com/getstattic/stattic/commit/0c25e5da5d2a37ca6b89ab6fe1217395fc713075)
- [🐛 BUG: Fixed session not found during Google Font download](https://github.com/getstattic/stattic/commit/43b797b854521e980186ea4bbb01bb70c53a20e2)
- [👌 IMPROVE: Updated HTTP requests with persistent session to optimize image and font downloads](https://github.com/getstattic/stattic/commit/b27feabd7c4536aae23e3f81dd6077c207c82af9)
- [👌 IMPROVE: Updated asset path if the --site-url flag is passed](https://github.com/getstattic/stattic/commit/46b01212529dd0e4e9b9760f1890f5adfef86e01)
- [👌 IMPROVE: Updated file processing to help with conversions to webp](https://github.com/getstattic/stattic/commit/ec209a225e44a08dc0f266061812a74ab9cc1412)
- [👌 IMPROVE: Updated gitignore to ignore output and templates folders](https://github.com/getstattic/stattic/commit/a8a7ed35287e81db40daedad0b24878165cd3d40)
- [👌 IMPROVE: Updated front matter post content](https://github.com/getstattic/stattic/commit/2692add3e2c4c4bd7ab1c71b1c272f6c6961068f)
- [👌 IMPROVE: Updated font file names to replace spaces with dashes](https://github.com/getstattic/stattic/commit/41719fbecf2f908dbfff43f658509f4eae36b0cd)
- [👌 IMPROVE: Updated templates to use stattic-content class for optional override of styles](https://github.com/getstattic/stattic/commit/918b9f6cdb236692544bb8265bcfd23bfc15902d)
- [👌 IMPROVE: Updated --fonts flag to use first font for body and second font for title](https://github.com/getstattic/stattic/commit/68979c5137c6ae0d4ce639920039bf9d0996af21)
- [👌 IMPROVE: Updated Google fonts to pull all available weights & gracefully skip unavailable weights](https://github.com/getstattic/stattic/commit/f273d7137008d314866339e39befdd1cbf7c09e4)
- [👌 IMPROVE: Removed unnecessary image file](https://github.com/getstattic/stattic/commit/87d30a54e7025bb1d0842314325f5d6593fc9853)
- [👌 IMPROVE: General code cleanup](https://github.com/getstattic/stattic/commit/b7fa7223e629a0c3c2fc62471589fce3d7f76471)
- [👌 IMPROVE: Updated title to conditionally use seo_title](https://github.com/getstattic/stattic/commit/7c9ebff9c3139491d8989be72914be8680b14e6c)
- [👌 IMPROVE: Updated webp processing to include featured_image from front matter](https://github.com/getstattic/stattic/commit/869ef7e28735eb83256dfb551328b31194b4cc96)
- [👌 IMPROVE: Updated various template styles](https://github.com/getstattic/stattic/commit/26e65c6d5eb8b0302ad801f1cd342f549c05e048)
- [👌 IMPROVE: Updated post content dates to reflect a new day](https://github.com/getstattic/stattic/commit/d4bdb6787476040752b0a0a68700c367509a4adf)
- [📖 DOC: Updated demo content](https://github.com/getstattic/stattic/commit/c989fedcc8f4288ced389784f97383d147be0727)
- [📖 DOC: Updated link in markdown content](https://github.com/getstattic/stattic/commit/d691923c9a35a83deeaf29d03c795b2eaa9ccaa3)

## 0.1.0

* [📦 NEW: Added pagination to the core theme's index and category template](https://github.com/getstattic/stattic/commit/c5fec466975c6fbab48ec1dc859512dee05a20ca)
* [👌 IMPROVE: Updated index page to collect all metadata found in the front matter](https://github.com/getstattic/stattic/commit/2d4c9ac084fb3915924af79b9284d93c9a0e8cd2)
* [👌 IMPROVE: Updated the 'time taken' in the log file to show 6 decimal places for more accurate readings](https://github.com/getstattic/stattic/commit/6720a111c3c4e8e6fb4a60c5d13cced62d92b486)
* [👌 IMPROVE: Updated template files to remove '.html' from hrefs](https://github.com/getstattic/stattic/commit/47596091773809e8a22f46c4ce535b67175db424)
* [👌 IMPROVE: Updated concurrency-based build approach to increase speed](https://github.com/getstattic/stattic/commit/5638f49c8ca4dabfa61fb807c1119d7afc419fb6)
* [👌 IMPROVE: Updated jinja2 version to >= 3.1.6](https://github.com/getstattic/stattic/commit/266bdf73d90dda309701e5ca4c1a2a633be7f389)
* [👌 IMPROVE: Updated .skip-link style to improve A11Y score in page speed insights report](https://github.com/getstattic/stattic/commit/d25854f9ba51f2cbf1d99dd1fec454c0872cdf8e)
* [👌 IMPROVE: Updated blog slug to be customizable with --blog-slug](https://github.com/getstattic/stattic/commit/f0e8151d5936d3a92e63aa152eb215fbaf8347e4)
* [👌 IMPROVE: Updated what content is output in the terminal logging](https://github.com/getstattic/stattic/commit/ce1bb015304eadba946f7973e6712e21935d86d1)

## 0.0.8

*  [📦 NEW: Added --assets flag to serve assets from outside of Stattic](https://github.com/getstattic/stattic/commit/6524ce0f859826ce0bd4cebc153857be01967884)
* [👌 IMPROVE: Updated 404 title text to be centered](https://github.com/getstattic/stattic/commit/bf15991e9261358ff7a16edbfc989072cfb2723b)
* [👌 IMPROVE: Updated various template classes](https://github.com/getstattic/stattic/commit/80e90e9022cff09a67a24638d067ba8d1679ff17)
* [👌 IMPROVE: Updated date output and post sorting by date](https://github.com/getstattic/stattic/commit/ffa2603b9e5f2f1b61944aa63c0ce0afb8f71b5b)
* [👌 IMPROVE: Updated header and background styles in base.html](https://github.com/getstattic/stattic/commit/a1aab6c6a76fcac3f31ac5d7d3c81ed337657a92)
* [👌 IMPROVE: Updated post excerpt text color from gray-400 to slate-50](https://github.com/getstattic/stattic/commit/f54b8a89ab3daee4422d94c7d4dc049a5e30a6b2)
* [👌 IMPROVE: Updated ul and ol style types](https://github.com/getstattic/stattic/commit/fec02d8110436b4724968e59ee020aa34cccab2d)
* [👌 IMPROVE: Updated TailWindCSS to ^3.4.17](https://github.com/getstattic/stattic/commit/852fd89b3b3c4708e3ec2453d2d079b4fe9e0258)

## 0.0.7

* [📦 NEW: Added --content flag to pull content from outside of Stattic](https://github.com/getstattic/stattic/commit/941d17521dbf1108c227ab4151f0f86ebde312d9)
* [📦 NEW: Added featured images to the post and page templates](https://github.com/getstattic/stattic/commit/6c431a446c8af3162e616b2ddbd7e686d247de64)
* [📦 NEW: Added --templates flag to pull template files from outside of Stattic](https://github.com/getstattic/stattic/commit/a9e6c0264129b87da167ba96d90742834b5dbc18)
* [📦 NEW: Added --robots flag with public (default) and private options](https://github.com/getstattic/stattic/commit/121ff7c0896e3140a0a776d7c62a489191fb8ea1)
* [👌 IMPROVE: Updated tailwindcss build output location](https://github.com/getstattic/stattic/commit/dbbd82df1a7c462fd79ddafee5fc3f10c9cf2b54)
* [👌 IMPROVE: Updated CSS URL](https://github.com/getstattic/stattic/commit/d48824dfb3f6c51b97aac1a1b6dc61c3ea02dcb9)
* [👌 IMPROVE: Updated minified CSS file name](https://github.com/getstattic/stattic/commit/eda388941b36a2571c1fd54605828dbcd0657cac)
* [👌 IMPROVE: Updated base.html with canonical URL check](https://github.com/getstattic/stattic/commit/6740934814945c9aa89a15e243fd07376c4585e6)
* [👌 IMPROVE: Updated base.html with open graph tags](https://github.com/getstattic/stattic/commit/dfd39dd08263d516edcbc1b97738a7bea77c2772)