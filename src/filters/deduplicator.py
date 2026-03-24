def normalize_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def deduplicate_papers(papers):
    seen = set()
    results = []

    for p in papers:
        if p.doi:
            key = ("doi", normalize_text(p.doi))
        elif p.title:
            key = ("title", normalize_text(p.title))
        else:
            key = ("link", normalize_text(p.link))

        if key in seen:
            continue

        seen.add(key)
        results.append(p)

    return results