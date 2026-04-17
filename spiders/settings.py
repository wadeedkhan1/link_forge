# ── Bot identity ───────────────────────────────────────────────────────────────
BOT_NAME = "web-crawler"

# ── Spider location ────────────────────────────────────────────────────────────
SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

# ── Crawl depth ────────────────────────────────────────────────────────────────
# Maximum number of hops from the seed URL.
# depth=0 → seed only, depth=1 → seed + its links, depth=2 → one more level
DEPTH_LIMIT = 2

# ── Politeness ─────────────────────────────────────────────────────────────────
ROBOTSTXT_OBEY = True                # respect robots.txt (Scrapy handles this)
DOWNLOAD_DELAY = 1.0                 # wait 1 second between requests
RANDOMIZE_DOWNLOAD_DELAY = True      # randomise ±50% to look more human
CONCURRENT_REQUESTS = 4             # max parallel requests at once
CONCURRENT_REQUESTS_PER_DOMAIN = 2  # max parallel requests to one domain

# ── Pipelines & Middlewares ────────────────────────────────────────────────────
# Dict of pipeline class → priority (lower number runs first)
ITEM_PIPELINES = {
    "spiders.pipelines.DatabasePipeline": 300,
}

# Connect Wadeed's HTTP request logic (crawler/fetcher.py) to Abdul's Spider!
DOWNLOADER_MIDDLEWARES = {
    "spiders.middlewares.HybridFetcherMiddleware": 500,
}

# ── HTTP cache (optional speedup for development) ──────────────────────────────
# Caches responses to disk so re-runs don't re-fetch pages
HTTPCACHE_ENABLED = False   # set to True during development to speed up testing

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"          # options: DEBUG, INFO, WARNING, ERROR

# ── Misc ───────────────────────────────────────────────────────────────────────
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
