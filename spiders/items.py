import scrapy

class PageItem(scrapy.Item):
    """Represents one crawled web page."""
    url         = scrapy.Field()   # the page's URL
    title       = scrapy.Field()   # <title> content
    text        = scrapy.Field()   # visible body text
    status_code = scrapy.Field()   # HTTP response code
    depth       = scrapy.Field()   # hops from seed URL
    session_id  = scrapy.Field()   # the crawl session identifier
    images      = scrapy.Field()   # extracted image urls
    metadata    = scrapy.Field()   # extracted meta tags


class LinkItem(scrapy.Item):
    """Represents one hyperlink found on a page (an edge in the link graph)."""
    source_url  = scrapy.Field()   # page where the link was found
    target_url  = scrapy.Field()   # where the link points
    session_id  = scrapy.Field()   # the crawl session identifier
