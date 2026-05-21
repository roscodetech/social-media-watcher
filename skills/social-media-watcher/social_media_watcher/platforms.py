"""Per-platform adapter registry — URL recognition + platform quirks."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class PlatformAdapter:
    """How one platform deviates from the generic download path."""

    name: str
    hosts: tuple[str, ...]
    ytdlp_format_args: tuple[str, ...] = ()
    single_post_only: bool = False
    post_markers: tuple[str, ...] = ()


GENERIC = PlatformAdapter(name="generic", hosts=())

REGISTRY: tuple[PlatformAdapter, ...] = (
    PlatformAdapter(
        "tiktok", ("tiktok.com",), ("-S", "vcodec:h264"),
        single_post_only=True,
        post_markers=("/video/", "/photo/", "/t/", "vm.tiktok.com", "vt.tiktok.com"),
    ),
    PlatformAdapter(
        "youtube", ("youtube.com", "youtu.be"),
        single_post_only=True,
        post_markers=("/watch?", "/shorts/", "youtu.be/", "/live/"),
    ),
    PlatformAdapter("instagram", ("instagram.com",)),
    PlatformAdapter("facebook", ("facebook.com", "fb.watch")),
    PlatformAdapter("twitter", ("twitter.com", "x.com")),
    PlatformAdapter("reddit", ("reddit.com", "redd.it")),
    PlatformAdapter("bluesky", ("bsky.app",)),
    PlatformAdapter("pinterest", ("pinterest.com", "pin.it")),
    PlatformAdapter("twitch", ("twitch.tv",)),
    PlatformAdapter("vimeo", ("vimeo.com",)),
)


def _host(url: str) -> str:
    """Lowercased hostname of url, without port."""
    return (urlparse((url or "").strip()).netloc or "").lower().split(":")[0]


def _is_http_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def resolve(url: str) -> PlatformAdapter:
    """Return the adapter whose hosts match url, or the generic fallback."""
    host = _host(url)
    for adapter in REGISTRY:
        if any(host == h or host.endswith("." + h) for h in adapter.hosts):
            return adapter
    return GENERIC


def validate_url(url: str) -> tuple[str, PlatformAdapter]:
    """Return (cleaned url, adapter); raise ValueError on bad or non-post URLs."""
    cleaned = (url or "").strip()
    if not _is_http_url(cleaned):
        raise ValueError(f"Not a valid URL: {url!r}")
    adapter = resolve(cleaned)
    if adapter.single_post_only and not any(m in cleaned for m in adapter.post_markers):
        raise ValueError(
            f"URL does not point to a single {adapter.name} post "
            f"(looks like a profile or feed): {url!r}"
        )
    return cleaned, adapter
