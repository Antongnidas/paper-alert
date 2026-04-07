import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from src.models import Paper


def _build_html(papers: List[Paper]) -> str:
    rows = []
    for p in papers:
        authors = ", ".join(p.authors) if p.authors else "N/A"
        date_str = p.pub_date.strftime("%Y-%m-%d") if p.pub_date else "N/A"
        keywords = ", ".join(p.matched_keywords) if p.matched_keywords else ""
        rows.append(f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <b><a href="{p.link}" style="color:#1a73e8;text-decoration:none;">{p.title}</a></b><br>
            <span style="color:#555;font-size:13px;">{authors}</span><br>
            <span style="color:#888;font-size:12px;">{p.source} &nbsp;|&nbsp; {date_str}</span>
            {"<br><span style='color:#2e7d32;font-size:12px;'>Keywords: " + keywords + "</span>" if keywords else ""}
          </td>
        </tr>""")

    body = "\n".join(rows)
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
    <h2 style="color:#1a73e8;">Paper Alert — {len(papers)} paper(s) matched</h2>
    <table width="100%" cellspacing="0" cellpadding="0">
    {body}
    </table>
    <p style="color:#aaa;font-size:11px;margin-top:20px;">Sent by Paper Alert</p>
    </body></html>"""


def send_email(papers: List[Paper], email_cfg: dict) -> bool:
    """
    email_cfg keys:
      smtp_host, smtp_port, sender, password, recipients (list), subject (optional)
    Returns True on success.
    """
    if not papers:
        print("[Email] No papers to send.")
        return False

    recipients = email_cfg.get("recipients", [])
    if not recipients:
        print("[Email] No recipients configured.")
        return False

    subject = email_cfg.get("subject", f"Paper Alert: {len(papers)} new paper(s)")
    html_content = _build_html(papers)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_cfg["sender"]
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    port = int(email_cfg["smtp_port"])
    try:
        if port == 465:
            # SSL 直连
            with smtplib.SMTP_SSL(email_cfg["smtp_host"], port) as server:
                server.login(email_cfg["sender"], email_cfg["password"])
                server.sendmail(email_cfg["sender"], recipients, msg.as_string())
        else:
            # STARTTLS（587）
            with smtplib.SMTP(email_cfg["smtp_host"], port) as server:
                server.ehlo()
                server.starttls()
                server.login(email_cfg["sender"], email_cfg["password"])
                server.sendmail(email_cfg["sender"], recipients, msg.as_string())
        print(f"[Email] Sent to {recipients}")
        return True
    except Exception as e:
        print(f"[Email] Failed: {e}")
        return False
