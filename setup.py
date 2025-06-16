#!/usr/bin/env python3
"""
Setup script for Stattic - static site generator.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Dependencies are now defined in pyproject.toml

setup(
    name='stattic',
    version='1.0.0',
    author='Robert DeVore',
    author_email='me@robertdevore.com',
    description='A simple yet powerful static site generator written in Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/getstattic/stattic',
    packages=find_packages(),
    package_data={
        'stattic_pkg': [
            'templates/*.html',
            'templates/**/*.html',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    python_requires='>=3.8',
    # Dependencies are now defined in pyproject.toml
    entry_points={
        'console_scripts': [
            'stattic=stattic_pkg.cli:main',
        ],
    },
    keywords='static site generator, markdown, jinja2, blog, website',
    project_urls={
        'Bug Reports': 'https://github.com/getstattic/stattic/issues',
        'Source': 'https://github.com/getstattic/stattic',
        'Documentation': 'https://docs.stattic.site',
    },
)
