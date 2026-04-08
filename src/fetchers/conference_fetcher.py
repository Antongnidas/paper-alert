import re
import io
import urllib.request
from datetime import datetime, timezone
from typing import List
from src.models import Paper
from src.utils.proxy import get_proxy_handler

# URL patterns per conference
CONFERENCE_PATTERNS = {
    "wfa": re.compile(r"https?://westernfinance-portal\.org/viewpaper\?n=\d+"),
    "afa": re.compile(r"https?://(?:www\.)?afajof\.org/.*paper.*", re.IGNORECASE),
}


def _download_pdf_bytes(url: str) -> bytes:
    proxy_handler = get_proxy_handler()
    if proxy_handler:
        opener = urllib.request.build_opener(proxy_handler)
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    with opener.open(url, timeout=30) as resp:
        return resp.read()


def _detect_conference_type(url: str) -> str:
    url_lower = url.lower()
    if "westernfinance" in url_lower or "wfa" in url_lower:
        return "wfa"
    if "afa" in url_lower or "afajof" in url_lower:
        return "afa"
    return "generic"


def _clean_title(text: str) -> str:
    """Remove leading/trailing whitespace and common non-title prefixes."""
    text = text.strip()
    # Remove session headers like "Session 1:", "Paper:", numbering
    text = re.sub(r"^(Session\s*\d+[:\-]?\s*|Paper\s*\d+[:\-]?\s*|\d+\.\s*)", "", text, flags=re.IGNORECASE)
    return text.strip()


def fetch_conference(url: str, source_name: str, category: str) -> List[Paper]:
    """
    Download a conference agenda PDF and extract paper links + titles.
    Returns a list of Paper objects.
    """
    import pdfplumber

    print(f"  Downloading agenda PDF from {url}")
    try:
        pdf_bytes = _download_pdf_bytes(url)
    except Exception as e:
        print(f"  [conference fetch error] {e}")
        return []

    conf_type = _detect_conference_type(url)
    link_pattern = CONFERENCE_PATTERNS.get(conf_type, re.compile(r"https?://\S+"))

    papers = []
    seen_links = set()

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Extract hyperlinks with their bounding box text
                annots = page.annots or []
                words = page.extract_words() or []

                for annot in annots:
                    uri = annot.get("uri", "") or ""
                    if not link_pattern.search(uri):
                        continue
                    if uri in seen_links:
                        continue
                    seen_links.add(uri)

                    # Find words near the annotation bounding box to get title
                    x0, y0, x1, y1 = (
                        annot.get("x0", 0), annot.get("top", 0),
                        annot.get("x1", 999), annot.get("bottom", 999),
                    )
                    # Expand bbox slightly to capture full title text
                    nearby = [
                        w["text"] for w in words
                        if w["x0"] >= x0 - 5 and w["x1"] <= x1 + 200
                        and w["top"] >= y0 - 5 and w["bottom"] <= y1 + 5
                    ]
                    title = _clean_title(" ".join(nearby)) if nearby else uri

                    papers.append(Paper(
                        source=source_name,
                        category=category,
                        title=title,
                        link=uri,
                        retrieved_at=datetime.now(timezone.utc),
                    ))

    except Exception as e:
        print(f"  [PDF parse error] {e}")

    print(f"  Found {len(papers)} papers in {source_name}")
    return papers
