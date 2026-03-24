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
    # 优先从 links 里找 doi
    if hasattr(entry, "links"):
        for link_obj in entry.links:
            href = getattr(link_obj, "href", "")
            if "doi.org" in href:
                return href

    # fallback：从 link 里找
    link = getattr(entry, "link", "")
    if "doi.org" in link:
        return link

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