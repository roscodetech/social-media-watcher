"""Entry point: `python -m social_media_watcher <url>`."""
from __future__ import annotations

import sys

from social_media_watcher.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
