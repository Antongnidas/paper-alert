"""
Auto-discover conference agenda PDF URLs from official websites.
Usage: python main.py --find-agenda wfa
       python main.py --find-agenda afa
"""

import re
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

CONFERENCE_SITES = {
    "wfa": {
        "urls": [
            "https://westernfinance.org",
            "https://www.westernfinance.org/annual-meeting",
            "https://www.westernfinance.org/meetings",
        ],
        "allowed_domains": ["westernfinance.org"],
    },
    "afa": {
        "urls": [
            "https://www.afajof.org",
            "https://www.afajof.org/annual-meeting",
            "https://www.afajof.org/program",
        ],
        "allowed_domains": ["afajof.org", "afa.org"],
    },
}

# Keywords that suggest a link is an agenda/program PDF
AGENDA_KEYWORDS = re.compile(
    r"(program|agenda|schedule|session|paper|proceedings)", re.IGNORECASE
)


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


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _fetch_page(url: str) -> str | None:
    proxies = _get_proxies()
    try:
        resp = requests.get(url, proxies=proxies, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"  [HTTP {resp.status_code}] {url}")
    except Exception as e:
        print(f"  [fetch error] {url}: {e}")
    return None


def _find_pdf_links(html: str, base_url: str) -> list[dict]:
    """Find all PDF links in a page, scored by relevance to agenda/program."""
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)
        text = tag.get_text(strip=True)

        # Must be a PDF
        if not (full_url.lower().endswith(".pdf") or "pdf" in href.lower()):
            continue

        # Score by keyword matches in URL and link text
        score = 0
        combined = f"{href} {text}".lower()
        for kw in ["program", "agenda", "schedule"]:
            if kw in combined:
                score += 2
        for kw in ["session", "paper", "meeting"]:
            if kw in combined:
                score += 1
        # Boost recent years (2023-2026)
        import re as _re
        year_match = _re.search(r"(202[3-9])", combined)
        if year_match:
            score += int(year_match.group(1)) - 2022  # e.g. 2025 → +3, 2026 → +4

        candidates.append({
            "url": full_url,
            "text": text or href,
            "score": score,
        })

    # Sort by score descending
    return sorted(candidates, key=lambda x: x["score"], reverse=True)


def find_agenda(conf_key: str) -> str | None:
    """
    Try to auto-discover the agenda PDF for a conference.
    Returns the PDF URL if found, None otherwise.
    Prints candidates for user to review.
    """
    conf_key = conf_key.lower()
    if conf_key not in CONFERENCE_SITES:
        print(f"Unknown conference: {conf_key}. Supported: {list(CONFERENCE_SITES.keys())}")
        return None

    print(f"\nSearching for {conf_key.upper()} agenda PDF...")
    conf_cfg = CONFERENCE_SITES[conf_key]
    site_urls = conf_cfg["urls"]
    allowed_domains = conf_cfg["allowed_domains"]
    all_candidates = []
    visited = set()

    def _is_allowed(url):
        return any(d in url for d in allowed_domains)

    for site_url in site_urls:
        if site_url in visited:
            continue
        visited.add(site_url)
        print(f"  Checking {site_url}")
        html = _fetch_page(site_url)
        if not html:
            continue

        candidates = [c for c in _find_pdf_links(html, site_url) if _is_allowed(c["url"])]
        all_candidates.extend(candidates)

        # Also follow links that look like meeting/program pages (same domain only)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            text = tag.get_text(strip=True).lower()
            sub_url = urljoin(site_url, href)
            if not _is_allowed(sub_url):
                continue
            if sub_url in visited:
                continue
            if any(kw in text or kw in href.lower() for kw in ["program", "agenda", "annual meeting", "meeting"]):
                visited.add(sub_url)
                sub_html = _fetch_page(sub_url)
                if sub_html:
                    sub_candidates = [c for c in _find_pdf_links(sub_html, sub_url) if _is_allowed(c["url"])]
                    all_candidates.extend(sub_candidates)

    # Deduplicate by URL
    seen = set()
    unique = []
    for c in sorted(all_candidates, key=lambda x: x["score"], reverse=True):
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)

    if not unique:
        print(f"\n  No PDF links found on {conf_key.upper()} website.")
        print("  Please manually find the agenda PDF and paste the URL into sources.yaml.")
        return None

    print(f"\n  Found {len(unique)} PDF candidate(s):\n")
    for i, c in enumerate(unique[:5], 1):
        marker = " <-- best match" if i == 1 else ""
        print(f"  [{i}] (score={c['score']}) {c['text']}")
        print(f"       {c['url']}{marker}")

    best = unique[0]
    if best["score"] > 0:
        print(f"\n  Best match: {best['url']}")
        return best["url"]
    else:
        print("\n  No high-confidence match found. Please check the candidates above.")
        return None
