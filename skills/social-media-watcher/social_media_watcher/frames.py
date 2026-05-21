"""Frame extraction — scene-detect (short-form), cadence sampling (long-form), photo."""
from __future__ import annotations

import shutil
from pathlib import Path

from social_media_watcher import (
    FRAME_LONG_EDGE,
    IMAGE_EXTS,
    MIN_SCENE_FRAMES,
    SCENE_THRESHOLD,
)
from social_media_watcher.download import run

_SCALE = f"scale=-2:'min({FRAME_LONG_EDGE},ih)'"


def needs_even_sampling(scene_frame_count: int) -> bool:
    """True if scene detection produced too few frames to rely on."""
    return scene_frame_count < MIN_SCENE_FRAMES


def evenly_spaced_indices(total: int, max_count: int) -> list[int]:
    """Pick up to max_count indices spread evenly across range(total)."""
    if max_count <= 0 or total <= 0:
        return []
    if total <= max_count:
        return list(range(total))
    step = total / max_count
    return [min(total - 1, int(i * step)) for i in range(max_count)]


def even_frame_seconds(duration: float, max_frames: int) -> list[float]:
    """Timestamps (seconds) spread evenly across a video of the given duration."""
    if duration <= 0 or max_frames <= 0:
        return [0.0]
    step = duration / max_frames
    return [round(i * step, 3) for i in range(max_frames)]


def chapter_frame_seconds(
    chapters: list[dict], duration: float, max_frames: int
) -> list[float]:
    """Chronological timestamps including every chapter start, topped up with
    even sampling across the whole video, capped at max_frames."""
    starts = sorted({float(c["start"]) for c in chapters
                     if c.get("start") is not None and 0 <= c["start"] < duration})
    if len(starts) >= max_frames:
        keep = [starts[i] for i in evenly_spaced_indices(len(starts), max_frames)]
        return sorted(keep)
    extra = [s for s in even_frame_seconds(duration, max_frames) if s not in starts]
    room = max_frames - len(starts)
    return sorted(starts + extra[:room])


def _renumber_frames(raw_frames: list[Path], frames_dir: Path) -> list[Path]:
    """Rename kept raw frames to frame-NN.jpg; delete leftover raw frames."""
    final: list[Path] = []
    for idx, src in enumerate(raw_frames, start=1):
        dst = frames_dir / f"frame-{idx:02d}.jpg"
        src.replace(dst)
        final.append(dst)
    for leftover in frames_dir.glob("raw-*.jpg"):
        leftover.unlink()
    return final


def extract_frames_scene(
    video: Path, frames_dir: Path, max_frames: int, duration: float
) -> list[Path]:
    """Short-form: ffmpeg scene detection with an even-sampling fallback."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',{_SCALE}",
        "-vsync", "vfr", str(frames_dir / "raw-%03d.jpg"),
    ])
    raw = sorted(frames_dir.glob("raw-*.jpg"))
    if needs_even_sampling(len(raw)):
        for frame in raw:
            frame.unlink()
        fps = max(0.1, max_frames / max(duration, 1.0))
        run(["ffmpeg", "-y", "-i", str(video), "-vf", f"fps={fps:.4f},{_SCALE}",
             str(frames_dir / "raw-%03d.jpg")])
        raw = sorted(frames_dir.glob("raw-*.jpg"))
    kept = [raw[i] for i in evenly_spaced_indices(len(raw), max_frames)]
    return _renumber_frames(kept, frames_dir)


def extract_frames_at(video: Path, frames_dir: Path, seconds: list[float]) -> list[Path]:
    """Long-form: grab one frame at each timestamp via per-seek ffmpeg calls."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    final: list[Path] = []
    for idx, ts in enumerate(seconds, start=1):
        dst = frames_dir / f"frame-{idx:02d}.jpg"
        run([
            "ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", str(video),
            "-vf", _SCALE, "-frames:v", "1", str(dst),
        ])
        if dst.exists():
            final.append(dst)
    return final


def collect_photo_frames(
    dl_dir: Path, frames_dir: Path, max_frames: int
) -> list[Path]:
    """Copy carousel images from dl_dir into frames_dir as frame-NN.<ext>."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(p for p in dl_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    kept = [images[i] for i in evenly_spaced_indices(len(images), max_frames)]
    final: list[Path] = []
    for idx, src in enumerate(kept, start=1):
        dst = frames_dir / f"frame-{idx:02d}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        final.append(dst)
    return final
