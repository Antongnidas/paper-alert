import feedparser
from src.utils.proxy import get_proxy_handler


def fetch_rss(url: str, retries: int = 2):
    proxy_handler = get_proxy_handler()
    if proxy_handler:
        handlers = [proxy_handler]
    else:
        handlers = []

    for attempt in range(retries + 1):
        try:
            feed = feedparser.parse(url, handlers=handlers)
            return feed
        except Exception as e:
            if attempt < retries:
                print(f"  [retry {attempt+1}] {e}")
            else:
                print(f"  [fetch failed] {url}: {e}")
                return feedparser.FeedParserDict(entries=[])
