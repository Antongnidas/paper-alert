import feedparser


def fetch_rss(url: str, retries: int = 2):
    for attempt in range(retries + 1):
        try:
            feed = feedparser.parse(url)
            return feed
        except Exception as e:
            if attempt < retries:
                print(f"  [retry {attempt+1}] {e}")
            else:
                print(f"  [fetch failed] {url}: {e}")
                # 返回空 feed，让 main.py 继续处理其他源
                return feedparser.FeedParserDict(entries=[])
