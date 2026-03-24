import json
import pandas as pd


def papers_to_rows(papers):
    rows = []
    for p in papers:
        rows.append({
            "source": p.source,
            "category": p.category,
            "title": p.title,
            "authors": "; ".join(p.authors),
            "abstract": p.abstract or "",
            "pub_date": p.pub_date.isoformat() if p.pub_date else "",
            "link": p.link,
            "doi": p.doi or "",
            "matched_keywords": "; ".join(p.matched_keywords),
            "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else "",
            "raw_date_text": p.raw_date_text or "",
        })
    return rows


def write_csv(papers, output_path: str):
    rows = papers_to_rows(papers)
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_json(papers, output_path: str):
    rows = papers_to_rows(papers)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def write_markdown(papers, output_path: str):
    lines = ["# Paper Monitor Report", ""]

    if not papers:
        lines.append("No matched papers found.")
    else:
        current_source = None
        for p in papers:
            if p.source != current_source:
                current_source = p.source
                lines.append(f"## {current_source}")
                lines.append("")

            lines.append(f"- **{p.title}**")
            lines.append(f"  - Date: {p.pub_date.isoformat() if p.pub_date else ''}")
            lines.append(f"  - Keywords: {', '.join(p.matched_keywords)}")
            lines.append(f"  - Link: {p.link}")
            if p.authors:
                lines.append(f"  - Authors: {', '.join(p.authors)}")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))