from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def parse_html(html_content, base_url):
    """
    Parses the HTML content to extract the title, visible text, all outgoing hyperlinks,
    images, and comprehensive metadata.
    """
    if not html_content:
        return {"title": "No Title", "text": "", "links": [], "images": [], "metadata": {}}

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Extract title
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else 'No Title'
    
    # 2. Extract metadata
    metadata = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            metadata[name] = content.strip()
            
    # 3. Extract visible text
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator='\n', strip=True)
    
    # 4. Extract hyperlinks
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()
        next_url = urljoin(base_url, href)
        parsed = urlparse(next_url)
        if parsed.scheme in ('http', 'https'):
            links.append(next_url)

    # 5. Extract images
    images = []
    for img_tag in soup.find_all('img', src=True):
        src = img_tag['src'].strip()
        img_url = urljoin(base_url, src)
        images.append(img_url)
            
    return {
        "title": title, 
        "text": text, 
        "links": list(set(links)),
        "images": list(set(images)),
        "metadata": metadata
    }
