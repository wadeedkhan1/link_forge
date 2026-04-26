"""
  1. start_requests() sends the seed URL to Scrapy's scheduler
  2. Scrapy fetches it and calls parse() with the response
  3. parse() extracts data → yields Items (go to pipeline → DB)
  4. parse() also yields new Requests for discovered links
  5. Scrapy adds those to its queue and repeats from step 2
  6. Scrapy tracks depth automatically via response.meta['depth']
  7. DEPTH_LIMIT in settings.py stops the recursion

Using BFS

Run with:
  scrapy crawl web_spider -a seed_url=http://books.toscrape.com -a depth=2 -s SCRAPY_SETTINGS_MODULE=spiders.settings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from crawler.parser import parse_html
from spiders.items import PageItem, LinkItem
from storage.deduplicator import Deduplicator
import string
from rank_bm25 import BM25Plus

def tokenize(text):
    text = text.lower()
    for p in string.punctuation:
        text = text.replace(p, ' ')
    tokens = text.split()
    stop_words = {
        "this", "that", "with", "have", "from", "they", "will",
        "been", "were", "said", "each", "which", "their", "there",
        "what", "when", "more", "also", "into", "than", "then",
        "some", "would", "about", "your", "just", "book", "books",
        "a", "an", "the", "and", "or", "but", "if", "because", "as",
        "of", "at", "by", "for", "in", "out", "on", "to", "up", "is",
        "are", "was", "be", "it", "i", "we", "you", "he", "she"
    }
    return [t for t in tokens if t not in stop_words]


class WebSpider(scrapy.Spider):
    """
    Args (passed with -a):
        seed_url : The starting URL  (default: http://books.toscrape.com/)
        depth    : Max crawl depth   (default: 2)
    """

    name = "web_spider"

    def __init__(self, seed_url=None, depth=2, session_id="legacy", prompt="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.prompt = prompt
        self.prompt_tokens = tokenize(self.prompt)
        # Build BM25 corpus from the user query ONCE to avoid rebuilding for every page
        self.bm25 = BM25Plus([self.prompt_tokens]) if self.prompt_tokens else None
        self.bm25_threshold = 0.1  # Allow low scores but block completely irrelevant pages


        # Set seed URLs (comma separated)
        if seed_url:
            self.seed_urls = [u.strip() for u in seed_url.split(',')]
        else:
            self.seed_urls = ["http://books.toscrape.com/"]
            
        self.session_id = session_id

        # Set max depth (override settings.py DEPTH_LIMIT)
        self.custom_settings = {
            "DEPTH_LIMIT": int(depth)
        }

        # Extract domains from seed URLs so we don't crawl external sites
        self.allowed_domains = []
        for url in self.seed_urls:
            parsed = urlparse(url)
            if parsed.netloc and parsed.netloc not in self.allowed_domains:
                self.allowed_domains.append(parsed.netloc)
        
        self.start_urls = self.seed_urls

        self._seen = Deduplicator()

        self.logger.info(f"[Spider] Seed     : {self.seed_urls}")
        self.logger.info(f"[Spider] Domain   : {self.allowed_domains}")
        self.logger.info(f"[Spider] Max depth: {depth}")

    def start_requests(self):
        for url in self.start_urls:
            self._seen.mark_seen(url)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """
        Called for every fetched page.
        Yields Items (saved to DB) and new Requests (next pages to crawl).
        """
        current_depth = response.meta.get("depth", 0)
        url = response.url

        # Use our centralized parser to get text, title, links, images, and metadata!
        parsed_data = parse_html(response.text, url)
        
        # BM25 relevance check BEFORE saving or following links
        if self.bm25:
            page_tokens = tokenize(parsed_data["text"])
            if not page_tokens:
                self.logger.info(f"[Spider] Page {url} rejected: no text")
                return
            
            bm25_score = self.bm25.get_scores(page_tokens)[0]
            if bm25_score < self.bm25_threshold:
                self.logger.info(f"[Spider] Page {url} rejected due to low BM25 score ({bm25_score:.2f})")
                return
            self.logger.info(f"[Spider] Page {url} accepted with BM25 score {bm25_score:.2f}")

        # Yield page data → DatabasePipeline → SQLite
        yield PageItem(
            url         = url,
            title       = parsed_data["title"],
            text        = parsed_data["text"],
            status_code = response.status,
            depth       = current_depth,
            session_id  = self.session_id,
            images      = parsed_data["images"],
            metadata    = parsed_data["metadata"]
        )

        # Extract and follow links
        for next_url in parsed_data["links"]:
            parsed_url = urlparse(next_url)

            # Skip external domains (protocol scheme was already filtered in parse_html)
            if not any(parsed_url.netloc.endswith(d) for d in self.allowed_domains):
                continue

            # Limit depth for social media platforms
            social_media_domains = {"youtube.com", "facebook.com", "reddit.com", "instagram.com", "twitter.com", "x.com", "tiktok.com", "linkedin.com"}
            is_social_media = any(parsed_url.netloc.endswith(d) for d in social_media_domains)
            
            if is_social_media and current_depth >= 1:
                continue

            # Save the link edge (for the link graph)
            yield LinkItem(source_url=url, target_url=next_url, session_id=self.session_id)

            # Enqueue unseen URLs
            if not self._seen.is_seen(next_url):
                self._seen.mark_seen(next_url)
                yield scrapy.Request(next_url, callback=self.parse)
