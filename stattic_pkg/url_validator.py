"""
URL Validation and SSRF Prevention Module for Stattic
This module provides comprehensive URL validation to prevent Server-Side Request Forgery (SSRF) attacks.
"""

import ipaddress
import socket
import re
from urllib.parse import urlparse
from typing import Union, Tuple, List, Set


class URLValidator:
    """
    Comprehensive URL validator to prevent SSRF attacks and validate URL safety.
    """
    
    # Allowed URL schemes
    ALLOWED_SCHEMES: Set[str] = {'http', 'https'}
    
    # Private/Reserved IP ranges to block (RFC 1918, RFC 3927, RFC 6598, etc.)
    BLOCKED_IP_RANGES: List[str] = [
        '0.0.0.0/8',          # "This network"
        '10.0.0.0/8',         # Private network (RFC 1918)
        '100.64.0.0/10',      # Carrier-grade NAT (RFC 6598)
        '127.0.0.0/8',        # Loopback (RFC 3330)
        '169.254.0.0/16',     # Link-local (RFC 3927)
        '172.16.0.0/12',      # Private network (RFC 1918)
        '192.0.0.0/24',       # IETF Protocol Assignments (RFC 6890)
        '192.0.2.0/24',       # Documentation (RFC 5737)
        '192.88.99.0/24',     # 6to4 Relay Anycast (RFC 3068)
        '192.168.0.0/16',     # Private network (RFC 1918)
        '198.18.0.0/15',      # Benchmark (RFC 2544)
        '198.51.100.0/24',    # Documentation (RFC 5737)
        '203.0.113.0/24',     # Documentation (RFC 5737)
        '224.0.0.0/4',        # Multicast (RFC 3171)
        '240.0.0.0/4',        # Reserved (RFC 1112)
        '255.255.255.255/32', # Broadcast
        # IPv6 ranges
        '::1/128',            # IPv6 loopback
        '::/128',             # IPv6 unspecified
        '::ffff:0:0/96',      # IPv4-mapped IPv6
        'fe80::/10',          # IPv6 link-local
        'fc00::/7',           # IPv6 unique local
        'ff00::/8',           # IPv6 multicast
    ]
    
    # Blocked hostnames/domains
    BLOCKED_HOSTNAMES: Set[str] = {
        'localhost',
        'localhost.localdomain',
        'ip6-localhost',
        'ip6-loopback',
        'broadcasthost',
        '0.0.0.0',
        '127.0.0.1',
        '::1',
        'metadata.google.internal',  # GCP metadata service
        '169.254.169.254',           # AWS/Azure metadata service
    }
    
    # Allowed domains for specific services (Google Fonts, etc.)
    ALLOWED_DOMAINS: Set[str] = {
        'fonts.googleapis.com',
        'fonts.gstatic.com',
    }
    
    def __init__(self, max_redirects: int = 5, timeout: int = 10):
        """
        Initialize URL validator.
        
        Args:
            max_redirects: Maximum number of redirects to follow
            timeout: Timeout for DNS resolution in seconds
        """
        self.max_redirects = max_redirects
        self.timeout = timeout
        self._blocked_networks = [ipaddress.ip_network(cidr) for cidr in self.BLOCKED_IP_RANGES]
    
    def validate_url(self, url: str, allowed_domains: Set[str] = None) -> Tuple[bool, str]:
        """
        Validate a URL for SSRF safety.
        
        Args:
            url: The URL to validate
            allowed_domains: Optional set of specifically allowed domains
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic URL parsing
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            # Check URL scheme
            if parsed.scheme.lower() not in self.ALLOWED_SCHEMES:
                return False, f"Unsupported URL scheme: {parsed.scheme}"
            
            # Extract hostname
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid hostname in URL"
            
            # Check against blocked hostnames
            if hostname.lower() in self.BLOCKED_HOSTNAMES:
                return False, f"Blocked hostname: {hostname}"
            
            # Check domain whitelist if provided
            if allowed_domains:
                domain_allowed = any(
                    hostname.lower() == domain.lower() or 
                    hostname.lower().endswith('.' + domain.lower())
                    for domain in allowed_domains
                )
                if not domain_allowed:
                    return False, f"Domain not in allowlist: {hostname}"
            
            # Resolve hostname to IP and validate
            try:
                ip_addresses = self._resolve_hostname(hostname)
                for ip_str in ip_addresses:
                    if not self._is_ip_allowed(ip_str):
                        return False, f"Blocked IP address: {ip_str}"
            except socket.gaierror:
                return False, f"Cannot resolve hostname: {hostname}"
            except Exception as e:
                return False, f"DNS resolution error: {str(e)}"
            
            # Additional URL pattern checks
            if not self._check_url_patterns(url):
                return False, "URL contains suspicious patterns"
            
            return True, "URL is valid"
            
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    def validate_google_fonts_url(self, url: str) -> Tuple[bool, str]:
        """
        Specifically validate Google Fonts URLs.
        
        Args:
            url: The Google Fonts URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Additional validation for Google Fonts API
        if 'fonts.googleapis.com' in url:
            if not re.match(r'https://fonts\.googleapis\.com/css2?\?', url):
                return False, "Invalid Google Fonts API URL format"
        elif 'fonts.gstatic.com' in url:
            if not re.match(r'https://fonts\.gstatic\.com/', url):
                return False, "Invalid Google Fonts static URL format"
        
        return self.validate_url(url, self.ALLOWED_DOMAINS)
    
    def _resolve_hostname(self, hostname: str) -> List[str]:
        """
        Resolve hostname to IP addresses.
        
        Args:
            hostname: The hostname to resolve
            
        Returns:
            List of IP addresses
        """
        try:
            # Get address info
            addr_info = socket.getaddrinfo(
                hostname, None, 
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                flags=socket.AI_ADDRCONFIG
            )
            
            # Extract unique IP addresses
            ip_addresses = list(set(info[4][0] for info in addr_info))
            return ip_addresses
            
        except socket.gaierror as e:
            raise e
    
    def _is_ip_allowed(self, ip_str: str) -> bool:
        """
        Check if an IP address is allowed (not in blocked ranges).
        
        Args:
            ip_str: IP address as string
            
        Returns:
            True if IP is allowed, False otherwise
        """
        try:
            ip = ipaddress.ip_address(ip_str)
            
            # Check against blocked networks
            for network in self._blocked_networks:
                if ip in network:
                    return False
            
            return True
            
        except ipaddress.AddressValueError:
            return False
    
    def _check_url_patterns(self, url: str) -> bool:
        """
        Check URL for suspicious patterns.
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL passes pattern checks, False otherwise
        """
        # Check for URL encoding that might hide malicious content
        suspicious_patterns = [
            r'%2f%2f',           # Double slash encoding
            r'%5c%5c',           # Double backslash encoding
            r'\.\./',            # Directory traversal
            r'%2e%2e%2f',        # Encoded directory traversal
            r'file://',          # File scheme
            r'ftp://',           # FTP scheme
            r'gopher://',        # Gopher scheme
            r'data://',          # Data scheme
            r'javascript:',      # JavaScript scheme
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                return False
        
        # Check for @ in netloc (user info) but allow it in query parameters
        parsed = urlparse(url)
        if parsed.netloc and '@' in parsed.netloc:
            return False
        
        return True

class SafeRequestor:
    """
    Safe HTTP requestor that validates URLs before making requests.
    """

    def __init__(self, validator: URLValidator = None, session=None):
        """
        Initialize safe requestor.
        
        Args:
            validator: URL validator instance
            session: Requests session to use
        """
        self.validator = validator or URLValidator()
        self.session = session

    def safe_get(self, url: str, allowed_domains: Set[str] = None, **kwargs) -> Tuple[bool, Union[object, str]]:
        """
        Make a safe GET request after URL validation.

        Args:
            url: URL to request
            allowed_domains: Optional set of allowed domains
            **kwargs: Additional arguments for requests.get()

        Returns:
            Tuple of (success, response_or_error_message)
        """
        import requests

        # Validate URL
        is_valid, error_msg = self.validator.validate_url(url, allowed_domains)
        if not is_valid:
            return False, f"URL validation failed: {error_msg}"

        try:
            # Set safe defaults
            kwargs.setdefault('timeout', 10)
            kwargs.setdefault('allow_redirects', False)  # Disable redirects for security
            kwargs.setdefault('headers', {})

            # Add User-Agent if not present
            if 'User-Agent' not in kwargs['headers']:
                kwargs['headers']['User-Agent'] = 'Stattic/1.0.0 (Static Site Generator)'

            # For streaming requests, don't automatically raise for status
            # Let the caller handle the response checking
            stream_mode = kwargs.get('stream', False)

            # Make request
            if self.session:
                response = self.session.get(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)

            # Only raise for status if not streaming (streaming needs custom handling)
            if not stream_mode:
                response.raise_for_status()

            return True, response

        except requests.exceptions.RequestException as e:
            return False, f"HTTP request failed: {str(e)}"
        except Exception as e:
            return False, f"Request error: {str(e)}"

    def safe_google_fonts_get(self, url: str, **kwargs) -> Tuple[bool, Union[object, str]]:
        """
        Make a safe GET request specifically for Google Fonts.

        Args:
            url: Google Fonts URL to request
            **kwargs: Additional arguments for requests.get()

        Returns:
            Tuple of (success, response_or_error_message)
        """
        # Validate as Google Fonts URL
        is_valid, error_msg = self.validator.validate_google_fonts_url(url)
        if not is_valid:
            return False, f"Google Fonts URL validation failed: {error_msg}"

        # Set Google Fonts specific headers
        kwargs.setdefault('headers', {})
        kwargs['headers'].update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        return self.safe_get(url, self.validator.ALLOWED_DOMAINS, **kwargs)
