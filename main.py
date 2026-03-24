import yaml
from src.fetchers.rss_fetcher import fetch_rss
from src.parsers.rss_parser import parse_rss_entry
from src.filters.date_filter import filter_by_date
from src.filters.keyword_filter import filter_by_keywords
from src.storage.writer import write_csv, write_json
import os
from src.filters.deduplicator import deduplicate_papers
from src.storage.writer import write_csv, write_json, write_markdown
 

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
def source_matches_selection(source, selection):
    source_names = set(selection.get("source_names", []))
    categories = set(selection.get("categories", []))
    groups = set(selection.get("groups", []))
    tags = set(selection.get("tags", []))

    if not any([source_names, categories, groups, tags]):
        return True

    if source.get("name") in source_names:
        return True

    if source.get("category") in categories:
        return True

    if source.get("group") in groups:
        return True

    source_tags = set(source.get("tags", []))
    if tags and (source_tags & tags):
        return True

    return False

def main():
    config = load_yaml("config.yaml")
    sources_config = load_yaml("sources.yaml")

    selection = config.get("selection", {})
    enabled_sources = [
    s for s in sources_config["sources"]
    if s.get("enabled", True) and source_matches_selection(s, selection)
]
    all_papers = []

    for source in enabled_sources:
        if source["type"] != "rss":
            continue

        print(f"Fetching: {source['name']}")
        feed = fetch_rss(source["url"])

        for entry in feed.entries:
            try:
                paper = parse_rss_entry(
                    entry,
                    source_name=source["name"],
                    category=source.get("category", "")
                )
                all_papers.append(paper)
            except Exception as e:
                print(f"Failed parsing entry from {source['name']}: {e}")

    print(f"Total papers fetched: {len(all_papers)}")

    lookback_days = config.get("lookback_days", 14)
    include_keywords = config.get("keywords", {}).get("include", [])
    exclude_keywords = config.get("keywords", {}).get("exclude", [])

    papers_after_date = filter_by_date(all_papers, lookback_days)
    papers_after_keyword = filter_by_keywords(
        papers_after_date,
        include_keywords,
        exclude_keywords
    )

    print(f"After date filter: {len(papers_after_date)}")
    print(f"After keyword filter: {len(papers_after_keyword)}")

    for p in papers_after_keyword:
        print(f"[{p.source}] {p.title}")
        print(f"Date: {p.pub_date}")
        print(f"Matched: {p.matched_keywords}")
        print(f"Link: {p.link}")
        print("----")
    os.makedirs("outputs", exist_ok=True)
    write_csv(papers_after_keyword, "outputs/papers.csv")
    write_json(papers_after_keyword, "outputs/papers.json")
    print("Saved to outputs/papers.csv and outputs/papers.json")
    papers_final = deduplicate_papers(papers_after_keyword)
    print(f"After dedup: {len(papers_final)}")
    write_markdown(papers_final, "outputs/papers.md")



if __name__ == "__main__":
    main()