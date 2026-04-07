import yaml
import os
import sys
import argparse
from src.fetchers.rss_fetcher import fetch_rss
from src.fetchers.nber_fetcher import fetch_nber
from src.fetchers.conference_fetcher import fetch_conference
from src.fetchers.agenda_finder import find_agenda
from src.parsers.rss_parser import parse_rss_entry
from src.filters.date_filter import filter_by_date
from src.filters.keyword_filter import filter_by_keywords
from src.filters.deduplicator import deduplicate_papers
from src.storage.writer import write_csv, write_json, write_markdown
from src.notifiers.email_sender import send_email
from src.notifiers.wechat_sender import send_wechat
from src.downloaders.pdf_downloader import download_pdfs


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

    # --- Fetch all papers ---
    all_papers = []
    conference_sources = []  # track for optional PDF download later

    for source in enabled_sources:
        print(f"Fetching: {source['name']}")

        if source["type"] == "nber":
            papers = fetch_nber(
                source_name=source["name"],
                category=source.get("category", ""),
                lookback_days=config.get("lookback_days", 14),
            )
            all_papers.extend(papers)

        elif source["type"] == "conference":
            papers = fetch_conference(
                url=source["url"],
                source_name=source["name"],
                category=source.get("category", ""),
            )
            all_papers.extend(papers)
            if source.get("download_pdf", False):
                conference_sources.append((source, papers))

        elif source["type"] == "rss":
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
                    print(f"  [parse error] {source['name']}: {e}")

    print(f"\nTotal papers fetched: {len(all_papers)}")

    # --- Filter ---
    lookback_days = config.get("lookback_days", 14)
    include_keywords = config.get("keywords", {}).get("include", [])
    exclude_keywords = config.get("keywords", {}).get("exclude", [])

    # Conference papers have no pub_date — skip date filter for them
    journal_papers = [p for p in all_papers if p.pub_date is not None]
    conf_papers = [p for p in all_papers if p.pub_date is None]

    papers_after_date = filter_by_date(journal_papers, lookback_days) + conf_papers
    papers_after_keyword = filter_by_keywords(
        papers_after_date, include_keywords, exclude_keywords
    )
    papers_final = deduplicate_papers(papers_after_keyword)

    print(f"After date filter:    {len(papers_after_date)}")
    print(f"After keyword filter: {len(papers_after_keyword)}")
    print(f"After dedup:          {len(papers_final)}")

    for p in papers_final:
        print(f"\n[{p.source}] {p.title}")
        if p.pub_date:
            print(f"  Date:    {p.pub_date}")
        print(f"  Matched: {p.matched_keywords}")
        print(f"  Link:    {p.link}")

    # --- Save outputs ---
    os.makedirs("outputs", exist_ok=True)
    write_csv(papers_final, "outputs/papers.csv")
    write_json(papers_final, "outputs/papers.json")
    write_markdown(papers_final, "outputs/papers.md")
    print("\nSaved to outputs/")

    # --- Download PDFs for matched conference papers ---
    for source, source_papers in conference_sources:
        matched = [p for p in papers_final if p.source == source["name"]]
        if matched:
            out_dir = source.get("pdf_output_dir", f"outputs/pdfs/{source['short_name']}")
            print(f"\nDownloading {len(matched)} PDFs for {source['name']} → {out_dir}")
            download_pdfs(matched, out_dir)
        else:
            print(f"\nNo matched papers to download for {source['name']}")

    # --- Notifications ---
    notify_cfg = config.get("notify", {})

    email_cfg = notify_cfg.get("email", {})
    if email_cfg.get("enabled", False):
        send_email(papers_final, email_cfg)

    wechat_cfg = notify_cfg.get("wechat", {})
    if wechat_cfg.get("enabled", False):
        send_wechat(papers_final, wechat_cfg)


def cmd_find_agenda(conf_key: str):
    """
    Auto-discover agenda PDF URL and optionally update sources.yaml.
    """
    sources_path = "sources.yaml"
    pdf_url = find_agenda(conf_key)

    if not pdf_url:
        return

    # Ask user if they want to update sources.yaml
    print(f"\nDo you want to update sources.yaml with this URL? [y/N] ", end="")
    answer = input().strip().lower()
    if answer != "y":
        print("Not updated. You can paste the URL manually into sources.yaml.")
        return

    # Update sources.yaml
    with open(sources_path, "r", encoding="utf-8") as f:
        content = f.read()

    conf_upper = conf_key.upper()
    # Find the placeholder URL for this conference and replace it
    pattern = re.compile(
        r'(- name: "' + conf_upper + r'.*?url: ")[^"]*(")',
        re.DOTALL
    )
    new_content, count = pattern.subn(rf'\g<1>{pdf_url}\g<2>', content)

    if count == 0:
        print(f"  Could not find a {conf_upper} entry in sources.yaml to update.")
        print(f"  Please manually set the url to: {pdf_url}")
        return

    with open(sources_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  sources.yaml updated with {conf_upper} agenda URL.")
    print(f"  Remember to set 'enabled: true' for the {conf_upper} entry.")


if __name__ == "__main__":
    import re as re_module

    parser = argparse.ArgumentParser(description="Paper Alert")
    parser.add_argument(
        "--find-agenda",
        metavar="CONF",
        help="Auto-discover agenda PDF for a conference (e.g. wfa, afa)",
    )
    args = parser.parse_args()

    if args.find_agenda:
        import re
        cmd_find_agenda(args.find_agenda.lower())
    else:
        main()
