import feedparser
import urllib.request


def _get_proxy_handler():
    """Read proxy from git config or environment, return urllib handler."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "config", "--get", "http.proxy"],
            capture_output=True, text=True
        )
        proxy_url = result.stdout.strip()
        if proxy_url:
            return urllib.request.ProxyHandler({
                "http": proxy_url,
                "https": proxy_url,
            })
    except Exception:
        pass
    return None


def fetch_rss(url: str, retries: int = 2):
    proxy_handler = _get_proxy_handler()
    if proxy_handler:
        opener = urllib.request.build_opener(proxy_handler)
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
