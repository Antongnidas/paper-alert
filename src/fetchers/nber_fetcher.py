import requests
from datetime import datetime, timezone
from typing import List
from bs4 import BeautifulSoup
from src.models import Paper
from src.utils.proxy import get_proxy_dict

NBER_API = (
    "https://www.nber.org/api/v1/working_page_listing"
    "/contentType/working_paper/_/_/search"
    "?page={page}&perPage=50&sortBy=public_date"
)


def _strip_html(text: str) -> str:
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


def _parse_authors(raw_authors: list) -> List[str]:
    return [_strip_html(a) for a in raw_authors]


def _parse_date(display_date: str) -> datetime:
    """Parse 'April 2026' style dates."""
    try:
        return datetime.strptime(display_date, "%B %Y").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_nber(source_name: str, category: str, lookback_days: int = 30) -> List[Paper]:
    proxies = get_proxy_dict()
    headers = {"User-Agent": "Mozilla/5.0"}
    papers = []

    cutoff = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # fetch up to 3 pages (150 papers) to cover recent period
    for page in range(1, 4):
        try:
            resp = requests.get(
                NBER_API.format(page=page),
                headers=headers,
                proxies=proxies,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [NBER fetch error page {page}] {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            pub_date = _parse_date(item.get("displaydate", ""))
            authors = _parse_authors(item.get("authors", []))
            title = _strip_html(item.get("title", ""))
            abstract = _strip_html(item.get("abstract", ""))
            url_path = item.get("url", "")
            link = f"https://www.nber.org{url_path}" if url_path else ""

            paper = Paper(
                source=source_name,
                category=category,
                title=title,
                authors=authors,
                abstract=abstract,
                pub_date=pub_date,
                link=link,
                retrieved_at=datetime.now(timezone.utc),
                raw_date_text=item.get("displaydate", ""),
            )
            papers.append(paper)

    return papers
