import os
import re
import subprocess
import urllib.request
from typing import List
from src.models import Paper


def _get_proxies():
    try:
        result = subprocess.run(
            ["git", "config", "--get", "http.proxy"],
            capture_output=True, text=True
        )
        proxy_url = result.stdout.strip()
        if proxy_url:
            return {"http": proxy_url, "https": proxy_url}
    except Exception:
        pass
    return {}


def _safe_filename(title: str, max_len: int = 80) -> str:
    """Convert paper title to a safe filename."""
    name = re.sub(r'[\\/:*?"<>|]', "", title)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_len]


def download_pdfs(papers: List[Paper], output_dir: str) -> None:
    """
    Download PDFs for a list of papers.
    Skips files that already exist.
    """
    os.makedirs(output_dir, exist_ok=True)
    proxies = _get_proxies()

    if proxies:
        proxy_handler = urllib.request.ProxyHandler(proxies)
        opener = urllib.request.build_opener(proxy_handler)
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    total = len(papers)
    for i, paper in enumerate(papers, 1):
        filename = _safe_filename(paper.title or f"paper_{i}") + ".pdf"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"  [{i}/{total}] Skip (exists): {filename}")
            continue

        try:
            urllib.request.urlretrieve(paper.link, filepath)
            print(f"  [{i}/{total}] Downloaded: {filename}")
        except Exception as e:
            print(f"  [{i}/{total}] Failed: {filename} — {e}")
