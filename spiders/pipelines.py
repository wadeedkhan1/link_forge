"""
Flow:
  Spider yields PageItem/LinkItem
       ↓
  Pipeline.process_item() is called automatically by Scrapy
       ↓
  We save it to our SQLite database using storage/db.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from storage.db import insert_page, insert_link
from spiders.items import PageItem, LinkItem


class DatabasePipeline:
    """
    Saves crawled pages and links to SQLite.
    Scrapy calls process_item() for every item the spider yields.
    """

    def process_item(self, item, spider):
        if isinstance(item, PageItem):
            insert_page(
                url         = item["url"],
                title       = item["title"],
                text        = item["text"],
                status_code = item["status_code"],
                depth       = item["depth"],
                session_id  = item.get("session_id", "legacy"),
                images      = item.get("images", []),
                metadata    = item.get("metadata", {}),
            )
            spider.logger.debug(f"[Pipeline] Saved page: {item['url']}")

        elif isinstance(item, LinkItem):
            insert_link(
                source_url = item["source_url"],
                target_url = item["target_url"],
                session_id = item.get("session_id", "legacy"),
            )

        # IMPORTANT: always return the item so other pipelines can use it
        return item
