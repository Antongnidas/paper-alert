import requests
from typing import List
from src.models import Paper


def _build_markdown(papers: List[Paper]) -> str:
    lines = [f"## Paper Alert — {len(papers)} paper(s) matched\n"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.authors[:3]) if p.authors else "N/A"
        if p.authors and len(p.authors) > 3:
            authors += " et al."
        date_str = p.pub_date.strftime("%Y-%m-%d") if p.pub_date else "N/A"
        keywords = ", ".join(p.matched_keywords) if p.matched_keywords else ""
        lines.append(f"**{i}. [{p.title}]({p.link})**")
        lines.append(f"> {authors}")
        lines.append(f"> {p.source} | {date_str}")
        if keywords:
            lines.append(f"> Keywords: {keywords}")
        lines.append("")
    return "\n".join(lines)


def send_wechat(papers: List[Paper], wechat_cfg: dict) -> bool:
    """
    wechat_cfg keys:
      sckey  — Server酱的 SendKey (https://sct.ftqq.com/)
    Returns True on success.
    """
    if not papers:
        print("[WeChat] No papers to send.")
        return False

    sckey = wechat_cfg.get("sckey", "").strip()
    if not sckey:
        print("[WeChat] No sckey configured.")
        return False

    title = f"Paper Alert: {len(papers)} new paper(s)"
    desp = _build_markdown(papers)

    url = f"https://sctapi.ftqq.com/{sckey}.send"
    try:
        resp = requests.post(url, data={"title": title, "desp": desp}, timeout=15)
        data = resp.json()
        if data.get("code") == 0:
            print("[WeChat] Sent successfully.")
            return True
        else:
            print(f"[WeChat] API error: {data}")
            return False
    except Exception as e:
        print(f"[WeChat] Failed: {e}")
        return False
