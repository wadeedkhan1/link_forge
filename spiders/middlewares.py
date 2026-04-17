import sys
import os
from scrapy.http import HtmlResponse
from twisted.internet import threads

# Ensure crawler module is available so we can inject Wadeed's fetch_page
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crawler.fetcher import fetch_page

class HybridFetcherMiddleware:
    """
    A custom Downloader Middleware that overrides Scrapy's native HTTP fetcher.
    It routes all requests through Wadeed's `crawler.fetcher.fetch_page()`.
    Because fetch_page uses 'requests' and 'selenium' which are blocking (synchronous), 
    we use Twisted's deferToThread to prevent blocking the async Scrapy event loop.
    """
    
    def process_request(self, request, spider):
        # Bounce the blocking fetch_page call into a twisted background worker thread
        return threads.deferToThread(self._thread_fetch, request)

    def _thread_fetch(self, request):
        url = request.url
        
        # Core integration: Uses the smart heuristic fetcher which auto-boots Selenium if needed
        html, status_code = fetch_page(url)
        
        # If fetch_page completely fails, we simulate an HTTP 500 so Scrapy retries/drops it properly
        if html is None:
            return HtmlResponse(url=url, status=500, request=request)
            
        # Wrap Wadeed's raw HTML back into an official Scrapy Response object
        return HtmlResponse(
            url=url,
            status=status_code,
            body=html.encode('utf-8'),
            request=request
        )
