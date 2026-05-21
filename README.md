# Social Media Watcher

A Claude Code plugin that turns a social-media video URL into a structured
summary. Claude downloads the post, **watches** it (views keyframes + reads a
caption-first transcript), and writes the summary — all locally, no API keys.

## What it does

Given a video URL from TikTok, YouTube, Instagram, Facebook, X/Twitter, Reddit,
Bluesky, Pinterest, Twitch, Vimeo (or any other yt-dlp-supported site), the
`social-media-watcher` skill:

1. Downloads the post + metadata + subtitles with `yt-dlp`.
2. Extracts keyframes with `ffmpeg` — scene detection for short clips,
   chapter-aware sampling for long-form video.
3. Builds the transcript caption-first — reusing the platform's own subtitles
   when present, falling back to local OpenAI Whisper.
4. Has Claude view the frames + read the transcript and write a structured
   summary: beat-by-beat for short clips, section-by-section for long-form.

Every run saves a full artifact bundle to
`skills/social-media-watcher/output/<timestamp>-<platform>-<id>/`.

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | https://python.org |
| `yt-dlp`, `openai-whisper` | `pip install -r skills/social-media-watcher/requirements.txt` |
| `ffmpeg` | `winget install Gyan.FFmpeg` (Windows), `brew install ffmpeg` (macOS) |

## Install

```
/plugin marketplace add roscodetech/social-media-watcher
/plugin install social-media-watcher
```

## Usage

Paste a video URL and ask Claude to summarize it:

> Summarize this: https://www.youtube.com/watch?v=...

Or run the extractor directly (from `skills/social-media-watcher/`):

```
python -m social_media_watcher "<URL>" --max-frames 14 --whisper-model small
python -m social_media_watcher "<URL>" --cookies-from-browser chrome   # private content
```

## Development

```
pip install -r requirements-dev.txt
pytest -m "not integration"                                  # fast unit tests
SMW_TEST_SHORT_URL=<url> SMW_TEST_LONG_URL=<url> pytest -m integration
```

## Limitations

- Threads has no yt-dlp extractor; Snapchat is Spotlight-only; Telegram is
  embed-only; LinkedIn video support is limited.
- Private/bot-walled content needs `--cookies-from-browser`.
- Non-English audio is transcribed, not translated.

## License

MIT — see [LICENSE](LICENSE).
