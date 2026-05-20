# TikTok Watcher

A Claude Code plugin that turns a TikTok URL into a structured summary. Claude
downloads the post, **watches** it (views the keyframes and reads the
transcribed audio), and writes a summary — all locally, no API keys.

## What it does

Given a TikTok video or photo URL, the `tiktok-watcher` skill:

1. Downloads the post and its metadata with `yt-dlp`.
2. Extracts keyframes and audio with `ffmpeg`.
3. Transcribes the audio with local OpenAI Whisper.
4. Has Claude view the frames + read the transcript and write a structured
   summary (hook, content, on-screen text, spoken content, visual style, call
   to action, topic, takeaway).

Every run saves a full artifact bundle to
`skills/tiktok-watcher/output/<timestamp>-<video-id>/`:
`video.mp4`, `frames/`, `audio.wav`, `transcript.txt`, `transcript.json`,
`info.json`, `manifest.json`, `summary.md`.

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | https://python.org |
| `yt-dlp`, `openai-whisper` | `pip install -r skills/tiktok-watcher/requirements.txt` |
| `ffmpeg` | `winget install Gyan.FFmpeg` (Windows), `brew install ffmpeg` (macOS), or your package manager |

## Install

```
/plugin marketplace add roscodetech/tiktok-watcher
/plugin install tiktok-watcher
```

## Usage

Paste a TikTok URL and ask Claude to summarize it:

> Summarize this TikTok: https://www.tiktok.com/@user/video/1234567890

Or run the extractor directly:

```
python skills/tiktok-watcher/tiktok_watch.py "<TikTok URL>" --max-frames 14 --whisper-model small
```

## Development

```
pip install -r requirements-dev.txt
pytest -m "not integration"          # fast unit tests
TIKTOK_TEST_URL=<url> pytest -m integration   # end-to-end test
```

## Limitations

- Public posts only — no login/cookie support for private content.
- Photo/carousel posts are summarized from images + metadata (no transcript).
- Non-English audio is transcribed, not translated.

## License

MIT — see [LICENSE](LICENSE).
