"""social_media_watcher — download, watch, and summarize social-media video."""
from __future__ import annotations

__version__ = "0.2.0"

# --- Shared constants --------------------------------------------------------
REQUIRED_TOOLS = ("yt-dlp", "ffmpeg", "whisper")
SCENE_THRESHOLD = 0.3
MIN_SCENE_FRAMES = 4
DEFAULT_MAX_FRAMES = 14
LONG_FORM_MAX_FRAMES = 30
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_LONG_FORM_SECONDS = 600
FRAME_LONG_EDGE = 720
IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
