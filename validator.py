import requests
from urllib.parse import urlparse

class UrlNotValid(Exception):
    pass

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def validate_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise UrlNotValid("Invalid URL format")

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )
    except requests.exceptions.SSLError:
        # SSL edge case → still treat as reachable
        return
    except requests.exceptions.RequestException:
        raise UrlNotValid("Unable to reach website")

    if r.status_code >= 400:
        raise UrlNotValid(f"Website returned status code {r.status_code}")

    content_type = r.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise UrlNotValid("Website does not appear to be HTML")
