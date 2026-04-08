import subprocess
import urllib.request


def get_proxy_url():
    """Read HTTP proxy URL from git config. Returns URL string or None."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "http.proxy"],
            capture_output=True, text=True
        )
        url = result.stdout.strip()
        return url if url else None
    except Exception:
        return None


def get_proxy_dict():
    """Return requests-style proxy dict, e.g. {'http': '...', 'https': '...'}."""
    url = get_proxy_url()
    if url:
        return {"http": url, "https": url}
    return {}


def get_proxy_handler():
    """Return urllib ProxyHandler or None."""
    url = get_proxy_url()
    if url:
        return urllib.request.ProxyHandler({"http": url, "https": url})
    return None


def get_proxy_host_port():
    """Return (host, port) tuple for raw socket connections, or (None, None)."""
    url = get_proxy_url()
    if not url:
        return None, None
    url = url.replace("http://", "").replace("https://", "")
    try:
        host, port = url.rsplit(":", 1)
        return host, int(port)
    except Exception:
        return None, None
