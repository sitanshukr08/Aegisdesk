import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from requests.adapters import HTTPAdapter
from urllib3.util.connection import create_connection

from app.config.settings import settings
from aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.web_tools")

class SSRFViolationError(Exception):
    pass

def is_safe_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_unspecified or ip_obj.is_multicast:
            return False
        if str(ip_obj) == "0.0.0.0" or str(ip_obj) == "::":
            return False
        return True
    except Exception:
        return False

class DNSPinnedAdapter(HTTPAdapter):
    """Resolves DNS once, pins the IP, prevents rebinding, and preserves SNI."""
    def __init__(self, pinned_ip: str, **kwargs):
        self.pinned_ip = pinned_ip
        super().__init__(**kwargs)

    def get_connection(self, url, proxies=None):
        conn = super().get_connection(url, proxies)
        # We need to hook into the connection creation to override the resolved IP
        # without changing the URL's hostname which SNI relies upon.
        original_new_conn = conn._new_conn
        
        def _new_conn_wrapper():
            # Create connection bypassing DNS lookup for the hostname, using pinned IP directly.
            # We must pass the original host and port, but connect to the pinned_ip.
            # urllib3's create_connection handles (host, port)
            extra_kw = {}
            if hasattr(conn, 'source_address'):
                extra_kw['source_address'] = conn.source_address
            if hasattr(conn, 'socket_options'):
                extra_kw['socket_options'] = conn.socket_options
                
            return create_connection(
                (self.pinned_ip, conn.port),
                timeout=conn.timeout,
                **extra_kw
            )
        
        conn._new_conn = _new_conn_wrapper
        return conn

def safe_fetch(url: str, timeout: int = 10) -> requests.Response:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: No hostname")
        
    resolved_ip = socket.gethostbyname(hostname)
    
    if not is_safe_ip(resolved_ip):
        raise SSRFViolationError(f"Resolved IP {resolved_ip} is in a blocked internal range.")
        
    session = requests.Session()
    # The adapter forces TCP to the pinned IP but keeps TLS SNI intact
    adapter = DNSPinnedAdapter(pinned_ip=resolved_ip)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AegisDesk/1.0'}
    return session.get(url, headers=headers, timeout=timeout)

@tool
def scrape_web_page(url: str, query: str) -> str:
    """Use this to scrape a webpage or external wiki portal and extract information to answer a query. 
    Provide the URL to scrape, and the specific query you are trying to answer."""
    logger.debug(f"[WEB SCRAPER] Navigating to {url} to answer: {query}")
    
    try:
        response = safe_fetch(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit to 5000 characters to prevent token explosion
        extracted = text[:5000]
        
        return f"Successfully scraped {url}. Here is the raw content. Analyze it to answer the user's query:\n{extracted}"
    except SSRFViolationError as e:
        return f"Security Error: {e}"
    except Exception as e:
        logger.error(f"[WEB SCRAPER] Failed to scrape {url}: {e}")
        return f"Error scraping {url}: {str(e)}"

@tool
def search_internet(query: str) -> str:
    """Use this to search the internet for up-to-date information, news, or global facts.
    Provide a specific search query."""
    logger.debug(f"[WEB SEARCH] Searching internet for: {query}")
    try:
        if not settings.tavily_api_key:
            return "Error: TAVILY_API_KEY is not configured."
        
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_api_key, "query": query, "search_depth": "basic", "max_results": 3},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        results = [f"Source: {res.get('url')}\\nContent: {res.get('content')}" for res in data.get('results', [])]
        return "\\n\\n".join(results) if results else "No relevant results found."
    except Exception as e:
        logger.error(f"[WEB SEARCH] Failed: {e}")
        return f"Error searching internet: {str(e)}"

WEB_SCRAPING_TOOLS = [scrape_web_page, search_internet]

