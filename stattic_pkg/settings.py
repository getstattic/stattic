#!/usr/bin/env python3
"""
Settings loader for Stattic static site generator.
Supports configuration from stattic.yml, stattic.yaml, or stattic.json files.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional


class StatticSettings:
    """Load and manage Stattic configuration settings."""
    
    # Default configuration
    DEFAULT_SETTINGS = {
        'output': 'output',
        'content': 'content',
        'templates': 'templates',
        'assets': None,
        'posts_per_page': 5,
        'sort_by': 'date',
        'fonts': None,
        'site_title': None,
        'site_tagline': None,
        'site_url': None,
        'robots': 'public',
        'watch': False,
        'minify': False,
        'blog_slug': 'blog'
    }
    
    # Config file names to look for (in order of preference)
    CONFIG_FILES = ['stattic.yml', 'stattic.yaml', 'stattic.json']
    
    def __init__(self, config_dir: str = None):
        """
        Initialize settings loader.
        
        Args:
            config_dir: Directory to look for config files. Defaults to current directory.
        """
        self.config_dir = config_dir or os.getcwd()
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.config_file_path = None
        
    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from configuration file if it exists.
        
        Returns:
            Dictionary of configuration settings
        """
        config_file = self._find_config_file()
        
        if config_file:
            self.config_file_path = config_file
            try:
                loaded_settings = self._load_config_file(config_file)
                if loaded_settings:
                    # Merge with defaults, giving preference to loaded settings
                    self.settings.update(loaded_settings)
                    print(f"Loaded configuration from: {os.path.relpath(config_file)}")
            except Exception as e:
                print(f"Warning: Failed to load config file {config_file}: {e}")
        
        return self.settings.copy()
    
    def _find_config_file(self) -> Optional[str]:
        """
        Find the first available configuration file.
        
        Returns:
            Path to config file or None if not found
        """
        for filename in self.CONFIG_FILES:
            config_path = os.path.join(self.config_dir, filename)
            if os.path.exists(config_path):
                return config_path
        return None
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary of configuration settings
        """
        try:
            file_ext = os.path.splitext(config_path)[1].lower()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if file_ext in ['.yml', '.yaml']:
                    return yaml.safe_load(f) or {}
                elif file_ext == '.json':
                    return json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {file_ext}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading configuration file: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file {config_path}: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        except (IOError, OSError) as e:
            raise IOError(f"Error reading configuration file {config_path}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error loading configuration file {config_path}: {e}")
    
    def create_sample_config(self, file_format: str = 'yml') -> str:
        """
        Create a sample configuration file.
        
        Args:
            file_format: Format for config file ('yml', 'yaml', or 'json')
            
        Returns:
            Path to created sample config file
        """
        sample_config = {
            '# Stattic Configuration File': None,
            '# Configure your static site generator settings here': None,
            '': None,
            'site_url': 'https://example.com',
            'site_title': 'My Static Site',
            'site_tagline': 'Built with Stattic',
            '': None,
            '# Build settings': None,
            'output': 'output',
            'content': 'content', 
            'templates': 'templates',
            'assets': 'assets',
            'blog_slug': 'blog',
            '': None,
            '# Content settings': None,
            'posts_per_page': 5,
            'sort_by': 'date',  # date, title, author, order
            '': None,
            '# Styling': None,
            'fonts': ['Quicksand', 'Open Sans'],
            '': None,
            '# SEO settings': None,
            'robots': 'public',  # public or private
            '': None,
            '# Development settings': None,
            'minify': False,
            'watch': False
        }
        
        # Remove comment-only entries for JSON
        if file_format == 'json':
            sample_config = {k: v for k, v in sample_config.items() 
                           if not (k.startswith('#') or k == '')}
        
        filename = f'stattic.{file_format}'
        config_path = os.path.join(self.config_dir, filename)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if file_format in ['yml', 'yaml']:
                    # Custom YAML output with comments
                    f.write("# Stattic Configuration File\n")
                    f.write("# Configure your static site generator settings here\n\n")
                    f.write("# Site information\n")
                    f.write("site_url: https://example.com\n")
                    f.write("site_title: My Static Site\n")
                    f.write("site_tagline: Built with Stattic\n\n")
                    f.write("# Build settings\n")
                    f.write("output: output\n")
                    f.write("content: content\n")
                    f.write("templates: templates\n")
                    f.write("assets: assets\n")
                    f.write("blog_slug: blog\n\n")
                    f.write("# Content settings\n")
                    f.write("posts_per_page: 5\n")
                    f.write("sort_by: date  # date, title, author, order\n\n")
                    f.write("# Styling\n")
                    f.write("fonts:\n")
                    f.write("  - Quicksand\n")
                    f.write("  - Open Sans\n\n")
                    f.write("# SEO settings\n")
                    f.write("robots: public  # public or private\n\n")
                    f.write("# Development settings\n")
                    f.write("minify: false\n")
                    f.write("watch: false\n")
                elif file_format == 'json':
                    json.dump(sample_config, f, indent=2)
        except PermissionError:
            raise PermissionError(f"Permission denied creating configuration file: {config_path}")
        except (IOError, OSError) as e:
            raise IOError(f"Error writing configuration file {config_path}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error creating configuration file {config_path}: {e}")
        
        return config_path
    
    def merge_with_args(self, args_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge configuration settings with command-line arguments.
        Command-line arguments take precedence over config file settings.
        
        Args:
            args_dict: Dictionary of command-line arguments
            
        Returns:
            Merged configuration dictionary
        """
        merged = self.settings.copy()
        
        # Override with non-None command line arguments
        for key, value in args_dict.items():
            if value is not None:
                # Handle special cases
                if key == 'fonts' and isinstance(value, str):
                    # Convert comma-separated string to list
                    merged[key] = [font.strip() for font in value.split(',')]
                else:
                    merged[key] = value
        
        return merged
