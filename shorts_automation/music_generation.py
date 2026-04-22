from __future__ import annotations

from hashlib import sha1
from pathlib import Path
import random
import subprocess

from .ffmpeg_utils import resolve_ffmpeg
from .script_builder import VideoScript


# Chord tones per mood (frequencies in Hz)
_MOOD_PROFILES: dict = {
    "meditative": {
        "freqs": [130.81, 164.81, 196.00, 261.63, 329.63],  # C3 E3 G3 C4 E4
        "vol": 0.55,
        "lowpass": 800,
        "echo": "aecho=0.88:0.88:220:0.55",
    },
    "reflective": {
        "freqs": [110.00, 138.59, 164.81, 220.00, 277.18],  # A2 C#3 E3 A3 C#4
        "vol": 0.50,
        "lowpass": 650,
        "echo": "aecho=0.90:0.88:320:0.60",
    },
    "focused": {
        "freqs": [146.83, 184.99, 220.00, 293.66, 369.99],  # D3 F#3 A3 D4 F#4
        "vol": 0.52,
        "lowpass": 1000,
        "echo": "aecho=0.78:0.82:110:0.32",
    },
}


def generate_music(script: VideoScript, signature: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{signature}_bgm.m4a"
    if output_path.exists():
        return output_path

    seed = int(sha1(signature.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    profile = _MOOD_PROFILES.get(script.quote.bgm_mood, _MOOD_PROFILES["meditative"])

    # Pick 3 chord tones; slightly detune each for warmth
    freqs = rng.sample(profile["freqs"], 3)
    vol = profile["vol"]

    cmd = [resolve_ffmpeg(), "-y"]
    for freq in freqs:
        f = round(freq * (1 + rng.uniform(-0.005, 0.005)), 2)
        v = round(vol * rng.uniform(0.88, 1.0), 3)
        v2 = round(v * 0.40, 3)   # 2nd harmonic
        v3 = round(v * 0.18, 3)   # 3rd harmonic (adds warmth without harshness)
        # Harmonic synthesis: fundamental + overtones give a pad/bell-like timbre
        expr = f"{v}*sin(2*PI*{f}*t)+{v2}*sin(4*PI*{f}*t)+{v3}*sin(6*PI*{f}*t)"
        cmd.extend(["-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d=36"])

    n = len(freqs)
    mix_inputs = "".join(f"[{i}:a]" for i in range(n))
    fc = (
        f"{mix_inputs}amix=inputs={n}:normalize=1,"  # normalize=1 prevents clipping
        f"lowpass=f={profile['lowpass']},"
        f"{profile['echo']},"
        f"afade=t=in:st=0:d=3,afade=t=out:st=30:d=4[aout]"
    )
    cmd.extend([
        "-filter_complex", fc,
        "-map", "[aout]",
        "-t", "34",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path),
    ])
    subprocess.run(cmd, check=True)
    return output_path
