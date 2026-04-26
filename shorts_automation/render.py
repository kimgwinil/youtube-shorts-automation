from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import random
import subprocess
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from .ffmpeg_utils import resolve_ffmpeg
from .script_builder import VideoScript


IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aac"}


@dataclass
class RenderResult:
    video_path: Path
    metadata_path: Path


def render_short(
    script: VideoScript,
    background_dir: Path,
    output_dir: Path,
    font_file: Path,
    shorts_hashtags: str,
    background_override: Path | None = None,
    bgm_override: Path | None = None,
) -> RenderResult:
    background = background_override or _pick_background(background_dir, script)
    bgm = bgm_override or _pick_bgm(background_dir.parent / "music", script.quote.bgm_mood)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{timestamp}_{script.quote.author.lower().replace(' ', '_')}"
    video_path = output_dir / f"{stem}.mp4"
    metadata_path = output_dir / f"{stem}.json"

    line_overlays = [
        output_dir / f"{stem}_line_{index + 1}.png"
        for index in range(len(script.lines))
    ]
    author_overlay = output_dir / f"{stem}_author.png"

    for overlay_path, line in zip(line_overlays, script.lines):
        _render_text_overlay(
            line=line,
            font_file=font_file,
            output_path=overlay_path,
            anchor_y=1320,
            font_size=64,
            box_alpha=150,
        )

    _render_author_overlay(
        author_line=script.author_line,
        source_line=script.source_line,
        font_file=font_file,
        output_path=author_overlay,
    )

    title = (
        script.title
        if "#shorts" in script.title.lower()
        else f"{script.title} #Shorts"
    )
    description_hashtags = (
        shorts_hashtags
        if "#shorts" in shorts_hashtags.lower()
        else f"#Shorts {shorts_hashtags}"
    )
    metadata_path.write_text(
        json.dumps(
            {
                "title": title[:100],
                "description": f"{script.description}\n\n{description_hashtags}",
                "tags": script.tags,
                "author": script.quote.author,
                "source": script.quote.source,
                "quote": script.quote.quote,
                "interpretation": script.quote.interpretation,
                "mood": script.quote.mood,
                "visual_style": script.visual_style,
                "bgm_mood": script.quote.bgm_mood,
                "visual_prompt": script.visual_prompt,
                "image_prompt_en": script.image_prompt_en,
                "bgm_prompt_en": script.bgm_prompt_en,
                "background": str(background),
                "bgm": str(bgm) if bgm else None,
                "duration_seconds": script.total_duration,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    cmd = _build_render_cmd(
        background=background,
        bgm=bgm,
        line_overlays=line_overlays,
        author_overlay=author_overlay,
        output=video_path,
        duration=script.total_duration,
    )
    subprocess.run(cmd, check=True)
    return RenderResult(video_path=video_path, metadata_path=metadata_path)


def _pick_background(background_dir: Path, script: VideoScript) -> Path:
    candidates = []
    preferred_dir = background_dir / script.quote.mood / script.visual_style
    fallback_dir = background_dir / script.quote.mood

    for candidate_dir in [preferred_dir, fallback_dir]:
        if candidate_dir.exists():
            candidates.extend(
                [
                    path
                    for path in candidate_dir.iterdir()
                    if path.is_file() and path.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS
                ]
            )
        if candidates:
            break

    if not candidates:
        raise RuntimeError(f"배경 파일이 없습니다: {preferred_dir} 또는 {fallback_dir}")
    return random.choice(candidates)


def _pick_bgm(music_dir: Path, mood: str) -> Path | None:
    candidates = []
    preferred_dir = music_dir / mood
    fallback_dir = music_dir / "default"
    for candidate_dir in [preferred_dir, fallback_dir]:
        if candidate_dir.exists():
            candidates.extend(
                [
                    path
                    for path in candidate_dir.iterdir()
                    if path.is_file() and path.suffix.lower() in AUDIO_EXTS
                ]
            )
        if candidates:
            break
    return random.choice(candidates) if candidates else None


def _build_render_cmd(
    background: Path,
    bgm: Path | None,
    line_overlays: Sequence[Path],
    author_overlay: Path,
    output: Path,
    duration: float,
) -> List[str]:
    cmd = [resolve_ffmpeg(), "-y"]
    if background.suffix.lower() in IMAGE_EXTS:
        cmd.extend(["-loop", "1", "-i", str(background)])
    else:
        cmd.extend(["-stream_loop", "-1", "-i", str(background)])

    for overlay_path in line_overlays:
        cmd.extend(["-i", str(overlay_path)])
    cmd.extend(["-i", str(author_overlay)])
    if bgm:
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm)])

    filter_complex, video_map, audio_map = _filter_graph(
        num_line_overlays=len(line_overlays),
        has_bgm=bgm is not None,
        duration=duration,
    )
    cmd.extend(
        [
            "-t",
            f"{duration:.2f}",
            "-filter_complex",
            filter_complex,
            "-map",
            video_map,
        ]
    )
    if audio_map:
        cmd.extend(
            [
                "-map",
                audio_map,
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
            ]
        )
    else:
        cmd.append("-an")

    cmd.extend(
        [
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )
    return cmd


def _filter_graph(num_line_overlays: int, has_bgm: bool, duration: float) -> Tuple[str, str, str | None]:
    timings = _line_timings(num_line_overlays)
    parts = ["[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v0]"]
    current = "[v0]"
    for index, (start, end) in enumerate(timings, start=1):
        next_label = f"[v{index}]"
        parts.append(
            f"{current}[{index}:v]overlay=0:0:enable='between(t,{start:.2f},{end:.2f})'{next_label}"
        )
        current = next_label

    author_index = num_line_overlays + 1
    final_label = f"[v{author_index}]"
    parts.append(f"{current}[{author_index}:v]overlay=0:0{final_label}")

    audio_map = None
    if has_bgm:
        bgm_index = author_index + 1
        parts.append(
            f"[{bgm_index}:a]highpass=f=420,lowpass=f=5200,"
            "equalizer=f=120:t=q:w=1.5:g=-16,equalizer=f=200:t=q:w=2:g=-12,"
            f"volume=0.32,"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(duration - 2.0, 0):.2f}:d=2,"
            "dynaudnorm=f=150:g=1.5,alimiter=limit=0.85[aout]"
        )
        audio_map = "[aout]"

    return ";".join(parts), final_label, audio_map


def _line_timings(num_lines: int) -> List[Tuple[float, float]]:
    durations = [3.3] * num_lines
    timings: List[Tuple[float, float]] = []
    cursor = 0.0
    for duration in durations:
        timings.append((cursor, cursor + duration))
        cursor += duration + 0.25
    return timings


def _render_text_overlay(
    line: str,
    font_file: Path,
    output_path: Path,
    anchor_y: int,
    font_size: int,
    box_alpha: int,
) -> None:
    width, height = 1080, 1920
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_file), font_size)
    max_width = width - 180
    wrapped = _wrap_text(draw, line, font, max_width)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=18, align="center", stroke_width=3)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = anchor_y

    padding_x = 40
    padding_y = 28
    box = [
        x - padding_x,
        y - padding_y,
        x + text_width + padding_x,
        y + text_height + padding_y,
    ]
    draw.rounded_rectangle(box, radius=28, fill=(20, 25, 32, box_alpha))
    draw.multiline_text(
        (x, y),
        wrapped,
        font=font,
        fill=(255, 250, 245, 255),
        spacing=18,
        align="center",
        stroke_width=3,
        stroke_fill=(20, 25, 32, 255),
    )
    image.save(output_path)


def _render_author_overlay(
    author_line: str,
    source_line: str,
    font_file: Path,
    output_path: Path,
) -> None:
    width, height = 1080, 1920
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    author_font = ImageFont.truetype(str(font_file), 42)
    source_font = ImageFont.truetype(str(font_file), 30)

    label = author_line
    source = source_line
    box = [70, 80, 540, 230]
    draw.rounded_rectangle(box, radius=30, fill=(245, 240, 230, 210))
    draw.text((110, 108), label, font=author_font, fill=(35, 34, 30, 255))
    draw.text((112, 162), source, font=source_font, fill=(80, 74, 66, 255))
    image.save(output_path)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    words = text.split()
    if len(words) <= 1:
        return _wrap_chars(draw, text, font, max_width)

    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return "\n".join(lines)


def _wrap_chars(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    lines: List[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)
