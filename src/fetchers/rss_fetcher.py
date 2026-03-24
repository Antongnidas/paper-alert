import feedparser


def fetch_rss(url: str):
    feed = feedparser.parse(url)
    return feed