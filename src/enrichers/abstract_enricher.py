import re
import requests
from html import unescape
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.models import Paper
from src.utils.proxy import get_proxy_dict

CROSSREF_API = "https://api.crossref.org/works/{doi}"


def _is_real_abstract(text: str) -> bool:
    """Check if the text looks like a real abstract (not RSS filler metadata)."""
    if not text or len(text.strip()) < 80:
        return False
    filler_patterns = [
        r"Volume\s+\d+",
        r"Issue\s+\d+",
        r"Pages?\s+\d+",
        r"\bISSN\b",
        r"Ahead of Print",
    ]
    for pat in filler_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return False
    if "." not in text:
        return False
    return True


def _clean_jats_xml(text: str) -> str:
    """Strip JATS XML tags from CrossRef abstract."""
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return " ".join(text.split()).strip()


def _fetch_one(doi: str, mailto: str, proxies: dict,
               timeout: int) -> Optional[str]:
    """Fetch abstract for a single DOI from CrossRef API."""
    url = CROSSREF_API.format(doi=doi)
    params = {}
    if mailto:
        params["mailto"] = mailto
    try:
        resp = requests.get(url, params=params, proxies=proxies,
                            timeout=timeout)
        if resp.status_code != 200:
            return None
        abstract = resp.json().get("message", {}).get("abstract", "")
        if abstract:
            return _clean_jats_xml(abstract)
    except Exception:
        pass
    return None


def enrich_abstracts(papers: List[Paper], config: dict) -> None:
    """Enrich papers with real abstracts from CrossRef API."""
    crossref_cfg = config.get("crossref", {})
    mailto = crossref_cfg.get("mailto", "")
    timeout = crossref_cfg.get("timeout", 10)
    max_workers = crossref_cfg.get("max_concurrent", 5)
    skip_sources = set(crossref_cfg.get("skip_sources", []))

    proxies = get_proxy_dict()

    # Filter papers that need enrichment
    to_enrich = [
        p for p in papers
        if p.doi and not _is_real_abstract(p.abstract) and p.source not in skip_sources
    ]

    if not to_enrich:
        print("Abstract enrichment: no papers need enrichment")
        return

    print(f"Enriching abstracts for {len(to_enrich)} papers via CrossRef...")

    enriched = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_fetch_one, p.doi, mailto, proxies, timeout): p
            for p in to_enrich
        }
        for future in as_completed(futures):
            paper = futures[future]
            abstract = future.result()
            if abstract:
                paper.abstract = abstract
                enriched += 1

    print(f"Enriched {enriched}/{len(to_enrich)} abstracts from CrossRef")
