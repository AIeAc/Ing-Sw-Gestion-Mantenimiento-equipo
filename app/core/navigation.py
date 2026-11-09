from urllib.parse import urlsplit


def safe_local_url(value, fallback):
    """Return an internal URL or a known-safe fallback."""
    candidate = str(value or "").strip()
    if not candidate:
        return fallback

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc or not candidate.startswith("/"):
        return fallback
    if candidate.startswith("//") or "\\" in candidate:
        return fallback
    return candidate
