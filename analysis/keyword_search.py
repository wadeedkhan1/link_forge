"""
analysis/keyword_search.py
──────────────────────────
Keyword frequency analysis across all crawled pages.
Used by the Flask UI search bar to filter results.
"""

import re
from collections import Counter
from storage.db import get_all_pages, search_pages


def count_keyword_frequency(keyword: str, session_id=None) -> dict:
    """
    Searches all pages for a keyword and counts how many times
    it appears in each page's text.
    """
    pages = search_pages(keyword, session_id=session_id)
    results = []

    for page in pages:
        text = page["text"] or ""
        # Count occurrences — case insensitive
        count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
        results.append({
            "url":   page["url"],
            "title": page["title"],
            "text":  text[:300],   # preview of first 300 chars
            "count": count,
            "depth": page["depth"],
        })

    # Sort by frequency descending
    results.sort(key=lambda x: x["count"], reverse=True)
    return results


def top_words(n: int = 20, min_length: int = 4, session_id=None) -> list[tuple[str, int]]:
    """
    Finds the N most frequent words across ALL crawled pages.
    Ignores common stop words and short words.
    """
    STOP_WORDS = {
        "this", "that", "with", "have", "from", "they", "will",
        "been", "were", "said", "each", "which", "their", "there",
        "what", "when", "more", "also", "into", "than", "then",
        "some", "would", "about", "your", "just", "book", "books",
    }

    pages = get_all_pages(session_id=session_id)
    counter = Counter()

    for page in pages:
        text = page["text"] or ""
        # Extract words — only alphabetic, lowercased
        words = re.findall(r"[a-z]{" + str(min_length) + r",}", text.lower())
        for word in words:
            if word not in STOP_WORDS:
                counter[word] += 1

    return counter.most_common(n)
