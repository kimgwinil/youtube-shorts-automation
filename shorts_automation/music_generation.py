from __future__ import annotations

from hashlib import sha1
from pathlib import Path
import random
import subprocess

from .ffmpeg_utils import resolve_ffmpeg
from .script_builder import VideoScript


def generate_music(script: VideoScript, signature: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{signature}_bgm.m4a"
    seed = int(sha1(signature.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)

    mood_profiles = {
        "meditative": ([196, 247, 294], 0.018, 1200),
        "reflective": ([174, 220, 262], 0.02, 950),
        "focused": ([196, 293.66, 392], 0.022, 1450),
    }
    notes, base_volume, lowpass = mood_profiles.get(script.quote.bgm_mood, ([220, 330, 440], 0.02, 1100))

    layers = []
    cmd = [resolve_ffmpeg(), "-y"]
    for index, note in enumerate(notes):
        shifted_note = round(note * (1 + rng.uniform(-0.02, 0.02)), 2)
        cmd.extend(["-f", "lavfi", "-i", f"sine=frequency={shifted_note}:sample_rate=44100:duration=34"])
        volume = max(base_volume - index * 0.004 + rng.uniform(-0.002, 0.002), 0.008)
        delay = 400 + index * 900 + rng.randint(0, 500)
        layers.append(f"[{index}:a]volume={volume:.3f},adelay={delay}|{delay}[a{index}]")

    mix_inputs = "".join(f"[a{index}]" for index in range(len(notes)))
    cmd.extend(
        [
            "-filter_complex",
            ";".join(
                layers
                + [
                    f"{mix_inputs}amix=inputs={len(notes)},lowpass=f={lowpass},"
                    "afade=t=in:st=0:d=2,afade=t=out:st=29:d=3[aout]"
                ]
            ),
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]
    )
    subprocess.run(cmd, check=True)
    return output_path
