from datetime import datetime, timezone
from dateutil import parser as dt_parser
from src.models import Paper
import re
from html import unescape


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # 去 HTML tag
    text = re.sub(r"<.*?>", "", text)
    # HTML entity
    text = unescape(text)
    # 去多余空白
    return " ".join(text.split()).strip()


def _parse_authors(entry) -> list[str]:
    if hasattr(entry, "authors"):
        names = []
        for a in entry.authors:
            raw = getattr(a, "name", "")
            # 去换行、多空格、逗号
            name = " ".join(raw.split()).strip(" ,")
            if name:
                names.append(name)
        return names
    return []


def _parse_date(entry):
    date_candidates = [
        getattr(entry, "published", None),
        getattr(entry, "updated", None),
        getattr(entry, "created", None),
    ]

    for d in date_candidates:
        if d:
            try:
                dt = dt_parser.parse(d)

                # 👉 统一转 UTC（关键）
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)

                return dt, d
            except Exception:
                continue

    return None, None


def _extract_doi(entry):
    """Extract DOI from entry links. Checks doi.org URLs and /doi/ paths."""
    doi_pattern = re.compile(r"10\.\d{4,}/[^\s?#]+")

    # 收集所有候选 URL
    candidates = []
    if hasattr(entry, "links"):
        for link_obj in entry.links:
            href = getattr(link_obj, "href", "")
            if href:
                candidates.append(href)
    link = getattr(entry, "link", "")
    if link:
        candidates.append(link)

    for url in candidates:
        # 优先匹配 doi.org 链接
        if "doi.org" in url:
            match = doi_pattern.search(url)
            return match.group(0).rstrip(".,;") if match else url

    # fallback：从任意 URL 路径中提取 DOI 模式（如 /doi/10.xxxx/...）
    for url in candidates:
        if "/doi/" in url:
            match = doi_pattern.search(url)
            if match:
                return match.group(0).rstrip(".,;")

    return None


def parse_rss_entry(entry, source_name: str, category: str) -> Paper:
    pub_date, raw_date_text = _parse_date(entry)

    return Paper(
        source=source_name,
        category=category,
        title=_clean_text(getattr(entry, "title", "")),
        authors=_parse_authors(entry),
        abstract=_clean_text(getattr(entry, "summary", "")),
        pub_date=pub_date,
        link=getattr(entry, "link", "").strip(),
        doi=_extract_doi(entry),
        retrieved_at=datetime.now(timezone.utc),
        raw_date_text=raw_date_text,
    )