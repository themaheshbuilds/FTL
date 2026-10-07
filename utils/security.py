import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
}


def is_ip_private_or_reserved(ip_str: str) -> bool:
    """Check if an IP address string belongs to a private, loopback, or reserved range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_url_security(url: str) -> Tuple[bool, str]:
    """Validate URL against SSRF and unsafe protocols.
    
    Returns:
        (is_safe, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    parsed = urlparse(url.strip())

    # 1. Check scheme
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed."

    # 2. Hostname presence
    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."

    hostname_lower = hostname.lower()

    # 3. Check blocked hostnames
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, "Access to local or internal loopback hosts is prohibited."

    # 4. Check if direct IP is private/loopback/cloud metadata
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_private_or_reserved(str(ip)):
            return False, "Access to private or internal IP addresses is prohibited."
    except ValueError:
        # Hostname is a domain name, resolve DNS
        try:
            # Resolve to check if domain maps to internal IP
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for item in addr_info:
                sockaddr = item[4]
                resolved_ip = sockaddr[0]
                if is_ip_private_or_reserved(resolved_ip):
                    return False, "URL resolves to a restricted internal IP address."
        except socket.gaierror:
            # DNS resolution failure will be handled gracefully during HTTP connection
            pass
        except Exception:
            pass

    return True, ""
