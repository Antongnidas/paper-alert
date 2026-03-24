import re


def contains_whole_word(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def filter_by_keywords(papers, include_keywords, exclude_keywords=None):
    exclude_keywords = exclude_keywords or []
    results = []

    for p in papers:
        text = (p.title or "").lower()

        matched = [kw for kw in include_keywords if contains_whole_word(text, kw)]
        excluded = any(contains_whole_word(text, kw) for kw in exclude_keywords)

        if matched and not excluded:
            p.matched_keywords = matched
            results.append(p)

    return results