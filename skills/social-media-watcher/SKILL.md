---
name: social-media-watcher
description: Use when the user wants to summarize, analyze, or understand a video from any social platform — TikTok, YouTube, Instagram, Facebook, X/Twitter, Reddit, Bluesky, Pinterest, Twitch, Vimeo and more. Give it a URL and it downloads the post, views the keyframes, builds a caption-first transcript, and produces a structured summary plus a saved artifact bundle. Handles short clips and long-form video. Triggers on a pasted social-media video URL, "summarize this video", "what's in this TikTok / YouTube video / Reel".
---

# Social Media Watcher

Download a social-media video, genuinely watch it (view frames + read a
transcript), and write a structured summary — short-form beat-by-beat, long-form
chapter-by-chapter.

## Prerequisites

The extractor needs Python plus three CLI tools. Before running, confirm all of
these are on PATH: `python`, `yt-dlp`, `ffmpeg`, `whisper`.

If any are missing, tell the user how to install them and stop:
- `yt-dlp` and `whisper`: `pip install -r requirements.txt` (in this skill's directory)
- `ffmpeg`: `winget install Gyan.FFmpeg` (Windows) or the OS package manager

## Steps

1. **Get the URL.** Take the video URL from the user's message. If none was given,
   ask for one.

2. **Run the extractor.** From this skill's directory, run:

   ```
   python -m social_media_watcher "<URL>"
   ```

   Optional flags: `--max-frames N` (short-form keyframes, default 14),
   `--whisper-model NAME` (default `small`), `--long-form-threshold SECONDS`
   (default 600), and `--cookies-from-browser BROWSER` (e.g. `chrome`) for
   private or bot-walled posts.

   The script prints the output directory path as its final stdout line. If it
   exits non-zero, report the error verbatim and stop — non-zero means the post
   is private (suggest `--cookies-from-browser`), deleted, region-locked, or the
   URL was invalid.

3. **Read the manifest.** Read `<output-dir>/manifest.json`: `type`
   (`video`/`photo`), `form` (`short`/`long`), `platform`, the `frames` list,
   `transcript`, `transcript_source`, `has_speech`, `chapters`, and `metadata`.

4. **Watch the post.** Use the Read tool on **every** image in `manifest.frames`
   so you actually see the video. Read `<output-dir>/transcript.txt`.

5. **Summarize.**

   **If `form` is `short`** — write these sections:
   - **Hook** — what grabs attention in the opening seconds.
   - **Content** — beat-by-beat what happens.
   - **On-screen text** — captions/overlays visible in the frames.
   - **Spoken content** — what is said (from the transcript).
   - **Visual style** — format, editing, setting, aesthetic.
   - **Call to action** — what the creator asks the viewer to do, if anything.
   - **Topic & hashtags** — subject matter and tags.
   - **Takeaway** — a one-paragraph overall summary.

   **If `form` is `long`** — write:
   - **TL;DR** — 2-3 sentences on the whole video.
   - **Section-by-section** — one entry per item in `manifest.chapters` (or, if
     `chapters` is empty, per evenly-spaced segment): the chapter title, what it
     covers, and a reference to its frame.
   - **Key takeaways** — the main points a viewer should leave with.
   - **Topic & hashtags**.

6. **Save the summary.** Write the summary as `<output-dir>/summary.md`.

7. **Report back.** Print the summary in the chat and give the artifact bundle
   path. Note `transcript_source` if it is `whisper` (auto-transcribed) or `none`
   (silent / music-only).

## Notes

- Supported platforms include TikTok, YouTube, Instagram, Facebook, X/Twitter,
  Reddit, Bluesky, Pinterest, Twitch, and Vimeo; other yt-dlp-supported sites are
  attempted via a generic path.
- Photo/carousel posts have no video or audio — `frames/` holds the images.
- Non-English audio is transcribed in its original language (no translation).
- Each run creates a new timestamped directory under `output/`.
