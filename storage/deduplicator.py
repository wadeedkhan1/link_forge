"""
storage/deduplicator.py
───────────────────────
Tracks which URLs the crawler has already visited, so we never
fetch the same page twice. This is a core requirement of any crawler.

How it works:
  - Uses a Python set() stored in memory for O(1) lookups
  - Also normalises URLs before comparing (strips trailing slashes,
    lowercases scheme+host) so http://example.com/ and
    http://example.com are treated as the same page

Why a set and not just the DB?
  - Querying the DB every time we discover a new URL would be slow
  - A set lookup is O(1) vs O(log n) for a DB index lookup
  - The set is rebuilt from the DB on startup so it survives restarts
"""

from urllib.parse import urlparse, urlunparse


class Deduplicator:
    def __init__(self):
        # In-memory set of normalised URLs we've already seen
        self._seen: set[str] = set()

    def normalise(self, url: str) -> str:
        """
        Canonicalises a URL so minor variations are treated as equal.
        Examples:
          http://Example.COM/page/  →  http://example.com/page
          HTTP://example.com/page   →  http://example.com/page
        """
        parsed = urlparse(url.strip())
        # Lowercase the scheme and host
        normalised = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=parsed.path.rstrip('/')   # strip trailing slash
        )
        return urlunparse(normalised)

    def is_seen(self, url: str) -> bool:
        """Returns True if this URL has already been crawled."""
        return self.normalise(url) in self._seen

    def mark_seen(self, url: str):
        """Marks a URL as crawled so it won't be visited again."""
        self._seen.add(self.normalise(url))

    def load_from_db(self, db_urls: list[str]):
        """
        Pre-loads the seen-set from URLs already stored in the database.
        Call this at startup to resume a previous crawl session without
        re-visiting pages we already have.
        """
        for url in db_urls:
            self.mark_seen(url)
        print(f"[Deduplicator] Loaded {len(self._seen)} known URLs from DB.")

    def count(self) -> int:
        """Returns how many unique URLs have been seen."""
        return len(self._seen)
