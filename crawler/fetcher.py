import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def _needs_js_rendering(html):
    """
    Heuristics to determine if the page is a JavaScript SPA and failed
    to load its main content via static HTTP request.
    """
    if not html:
        return False
        
    soup = BeautifulSoup(html, 'lxml')
    
    # Heuristic 1: Look for common empty SPA mount points
    for mount_id in ["root", "app", "__next", "vue-app"]:
        element = soup.find(id=mount_id)
        if element and len(element.get_text(strip=True)) == 0 and len(element.find_all(recursive=False)) == 0:
            return True
            
    # Heuristic 2: Noscript warning indicating JS requirement
    noscript = soup.find('noscript')
    if noscript and 'enable javascript' in noscript.get_text(strip=True).lower():
        # Only true if there's very little visible text otherwise
        text_content = soup.get_text(strip=True)
        if len(text_content) < 200:
            return True
            
    # Heuristic 3: Very low text-to-script-tag ratio
    text_len = len(soup.get_text(separator=' ', strip=True))
    script_count = len(soup.find_all('script'))
    if text_len < 100 and script_count > 3:
        return True
        
    return False

def _fetch_dynamic(url, timeout=15):
    """Fallback fetcher using headless Selenium for JS processing."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    
    logger.info(f"[Fetcher] Booting headless browser for dynamic page: {url}")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        html = driver.page_source
        driver.quit()
        return html, 200
    except Exception as e:
        logger.error(f"[Fetcher] Selenium error for {url}: {e}")
        try:
            driver.quit()
        except:
            pass
        return None, None

def fetch_page(url, timeout=10):
    """
    Intelligent fetcher that automatically retrieves the page content.
    It defaults to fast pipelined `requests`, but seamlessly falls back
    to `Selenium` if it detects a JavaScript-rendered SPA.
    """
    logger.info(f"[Fetcher] Fetching: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        html, status = response.text, response.status_code
        
        # Determine if we got an empty SPA shell
        if _needs_js_rendering(html):
            logger.info(f"[Fetcher] Detected SPA/JS requirements. Switching to Selenium...")
            return _fetch_dynamic(url, timeout=15)
            
        return html, status
    except requests.RequestException as e:
        logger.error(f"[Fetcher] Request error for {url}: {e}")
        return None, None

