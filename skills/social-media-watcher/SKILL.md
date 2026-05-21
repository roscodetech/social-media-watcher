---
name: tiktok-watcher
description: Use when the user wants to summarize, analyze, or understand a TikTok video or photo post. Give it a TikTok URL and it downloads the post, views the keyframes, transcribes the spoken audio with local Whisper, and produces a structured summary plus a saved artifact bundle. Triggers on a pasted TikTok URL, "summarize this TikTok", "what's in this TikTok video", "watch this TikTok".
---

# TikTok Watcher

Download a TikTok post, genuinely watch it (view its frames + read its
transcribed audio), and write a structured summary.

## Prerequisites

The extractor needs Python plus three CLI tools. Before running, confirm all of
these are on PATH: `python`, `yt-dlp`, `ffmpeg`, `whisper`.

If any are missing, tell the user how to install them and stop:
- `yt-dlp` and `whisper`: `pip install -r requirements.txt` (in this skill's directory)
- `ffmpeg`: `winget install Gyan.FFmpeg` (Windows) or the OS package manager

## Steps

1. **Get the URL.** Take the TikTok URL from the user's message. If none was
   given, ask for one.

2. **Run the extractor.** From this skill's directory, run:

   ```
   python tiktok_watch.py "<URL>"
   ```

   Optional flags: `--max-frames N` (default 14), `--whisper-model NAME`
   (default `small`; use `tiny` for speed or `medium` for accuracy).

   The script prints the output directory path as its final stdout line. If it
   exits non-zero, report the error message to the user verbatim and stop — a
   non-zero exit means the post is private, deleted, region-locked, or the URL
   was invalid.

3. **Read the manifest.** Read `<output-dir>/manifest.json`. It contains the run
   `type` (`video` or `photo`), the ordered `frames` list, the `transcript`
   text, `has_speech`, and a `metadata` block (author, description, hashtags,
   duration, counts, music).

4. **Watch the post.** Use the Read tool on **every** image listed in
   `manifest.frames` so you actually see the video. Note on-screen text, visible
   actions, setting, people, products, and editing style as you go.

5. **Read the transcript.** If `has_speech` is true, read
   `<output-dir>/transcript.txt` for the spoken content. If false, the post is
   silent or music-only — say so in the summary.

6. **Write the summary.** Create `<output-dir>/summary.md` with these sections:
   - **Hook** — what grabs attention in the opening seconds.
   - **Content** — beat-by-beat what happens in the post.
   - **On-screen text** — captions and text overlays visible in the frames.
   - **Spoken content** — what is said (from the transcript).
   - **Visual style** — format, editing, setting, aesthetic.
   - **Call to action** — what the creator asks the viewer to do, if anything.
   - **Topic & hashtags** — subject matter and tags.
   - **Takeaway** — a one-paragraph overall summary.

7. **Report back.** Print the summary in the chat and tell the user where the
   full artifact bundle is saved (`<output-dir>/`), listing what it contains:
   `video.mp4`, `frames/`, `audio.wav`, `transcript.txt`, `transcript.json`,
   `info.json`, `manifest.json`, `summary.md`.

## Notes

- Photo/carousel posts have no video or audio — `frames/` holds the carousel
  images and there is no transcript. Summarize from the images and metadata.
- A non-English video is transcribed in its original language (no translation).
- Each run creates a new timestamped directory under `output/`; nothing is
  overwritten.
