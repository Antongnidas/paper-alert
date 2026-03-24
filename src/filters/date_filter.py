from datetime import datetime, timedelta, timezone


def filter_by_date(papers, lookback_days: int):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)

    results = []
    for p in papers:
        if not p.pub_date:
            continue

        pub = p.pub_date
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)

        if pub >= cutoff:
            results.append(p)

    return results