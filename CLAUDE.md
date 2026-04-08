# Paper Alert

Academic paper monitoring tool that fetches, filters, and notifies about new papers.

## Architecture

```
main.py                          # Entry point: fetch → enrich → filter → output → notify
config.yaml                     # User config (gitignored, contains credentials)
config.example.yaml             # Config template
sources.yaml                    # Journal/conference definitions
src/
  models.py                     # Paper dataclass
  fetchers/
    rss_fetcher.py              # RSS feed fetcher (feedparser)
    nber_fetcher.py             # NBER API fetcher
    conference_fetcher.py       # PDF agenda parser (pdfplumber)
    agenda_finder.py            # Auto-discover conference agenda URLs
  enrichers/
    abstract_enricher.py        # CrossRef API abstract enrichment (concurrent)
  parsers/
    rss_parser.py               # RSS entry → Paper object, DOI extraction
  filters/
    date_filter.py              # Lookback days filter
    keyword_filter.py           # Include/exclude keywords, supports title_only/title_and_abstract
    deduplicator.py             # Dedup by DOI/title/link
  storage/
    writer.py                   # CSV, JSON, Markdown output
  notifiers/
    email_sender.py             # Gmail SMTP with HTTP CONNECT proxy tunnel
    wechat_sender.py            # Server酱 WeChat push
  downloaders/
    pdf_downloader.py           # Download matched conference PDFs
  utils/
    proxy.py                    # Centralized proxy config (reads from git config)
```

## Pipeline Flow

1. Load config.yaml + sources.yaml
2. Fetch papers from enabled sources (RSS / NBER API / Conference PDF)
3. Date filter (lookback_days)
4. Abstract enrichment via CrossRef API (for papers with DOI but no real abstract)
5. Keyword filter (title_only or title_and_abstract)
6. Deduplication
7. Output (CSV/JSON/Markdown → outputs/)
8. Notifications (Email / WeChat)
9. Optional PDF download for conference papers

## Key Design Decisions

- Proxy is read from `git config --get http.proxy`, centralized in `src/utils/proxy.py`
- Email uses HTTP CONNECT tunnel through proxy for restricted networks
- CrossRef enrichment runs after date filter, before keyword filter (minimize API calls)
- Conference papers have no pub_date, skip date filter
- config.yaml is gitignored (contains credentials), config.example.yaml is the template

## Commands

```bash
python main.py                    # Run full pipeline
python main.py --find-agenda wfa  # Auto-discover WFA agenda URL
python main.py --find-agenda afa  # Auto-discover AFA agenda URL
```

## Dependencies

All in requirements.txt: feedparser, requests, beautifulsoup4, python-dateutil, pandas, pyyaml, lxml, pdfplumber
