from langchain_core.tools import tool
import requests
import socket
import ipaddress
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src.aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.web_tools")

def is_safe_url(url: str) -> bool:
    """SSRF Protection: Resolves the domain and blocks internal IP spaces."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
            
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            logger.warning(f"SSRF Alert: Blocked attempt to scrape internal IP {ip}")
            return False
        return True
    except Exception as e:
        logger.error(f"URL resolution failed: {e}")
        return False

@tool
def scrape_web_page(url: str, query: str) -> str:
    """Use this to scrape a webpage or internal wiki portal and extract information to answer a query. 
    Provide the URL to scrape, and the specific query you are trying to answer."""
    logger.debug(f"[WEB SCRAPER] Navigating to {url} to answer: {query}")
    
    if not is_safe_url(url):
        return f"Security Error: The URL {url} resolves to a private or blocked internal IP space. Access Denied."
        
    try:
        # We use a standard User-Agent to prevent 403 blocks
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AegisDesk/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit to 5000 characters to prevent token explosion
        extracted = text[:5000]
        
        return f"Successfully scraped {url}. Here is the raw content. Analyze it to answer the user's query:\n{extracted}"
    except Exception as e:
        logger.error(f"[WEB SCRAPER] Failed to scrape {url}: {e}")
        return f"Error scraping {url}: {str(e)}"

WEB_SCRAPING_TOOLS = [scrape_web_page]
