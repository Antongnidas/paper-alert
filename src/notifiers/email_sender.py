import smtplib
import socket
import ssl
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from src.models import Paper


def _get_proxy():
    """Read proxy host/port from git config."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "http.proxy"],
            capture_output=True, text=True
        )
        proxy_url = result.stdout.strip()
        if not proxy_url:
            return None, None
        proxy_url = proxy_url.replace("http://", "").replace("https://", "")
        host, port = proxy_url.rsplit(":", 1)
        return host, int(port)
    except Exception:
        return None, None


def _connect_via_proxy(smtp_host: str, smtp_port: int):
    """
    Open a TCP tunnel through an HTTP CONNECT proxy,
    then return an SSL-wrapped socket ready for smtplib.
    """
    proxy_host, proxy_port = _get_proxy()
    if not proxy_host:
        return None

    # Connect to proxy
    raw = socket.create_connection((proxy_host, proxy_port), timeout=15)
    # Send HTTP CONNECT
    connect_req = f"CONNECT {smtp_host}:{smtp_port} HTTP/1.1\r\nHost: {smtp_host}:{smtp_port}\r\n\r\n"
    raw.sendall(connect_req.encode())
    # Read response
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += raw.recv(4096)
    if b"200" not in resp:
        raw.close()
        raise ConnectionError(f"Proxy CONNECT failed: {resp[:100]}")
    # Wrap with SSL
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(raw, server_hostname=smtp_host)


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

    smtp_host = email_cfg["smtp_host"]
    port = int(email_cfg["smtp_port"])
    try:
        # Try tunneling through proxy first (needed on restricted networks)
        sock = _connect_via_proxy(smtp_host, port)
        if sock:
            # Manually init SMTP_SSL with pre-connected SSL socket
            server = smtplib.SMTP_SSL.__new__(smtplib.SMTP_SSL)
            smtplib.SMTP.__init__(server, timeout=15)
            server.sock = sock
            server.file = sock.makefile("rb")
            server._tls_established = True
            code, msg_bytes = server.getreply()
            if code != 220:
                raise ConnectionError(f"SMTP greeting failed: {code} {msg_bytes}")
        elif port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port)
        else:
            server = smtplib.SMTP(smtp_host, port)
            server.ehlo()
            server.starttls()

        with server:
            server.login(email_cfg["sender"], email_cfg["password"])
            server.sendmail(email_cfg["sender"], recipients, msg.as_string())
        print(f"[Email] Sent to {recipients}")
        return True
    except Exception as e:
        print(f"[Email] Failed: {e}")
        return False
