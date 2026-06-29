from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

from .daily_context import DailyContext
from .script_builder import EssayScript
from .state_store import load_state


ESSAY_TOPICS = [
    # 감정·관계
    "사랑", "그리움", "이별", "만남", "설렘", "눈물", "웃음", "위로",
    "용서", "신뢰", "배려", "친절", "감사", "공감", "연대", "우정",
    "가족", "부모", "자녀", "고독", "외로움", "그리움", "포용",
    # 내면·성장
    "용기", "희망", "꿈", "믿음", "자존", "겸손", "인내", "끈기",
    "성장", "변화", "도전", "실패", "회복", "치유", "자유", "해방",
    "정직", "성실", "집중", "휴식", "균형", "비움", "내려놓음",
    # 시간·자연
    "아침", "새벽", "황혼", "밤", "봄", "여름", "가을", "겨울",
    "비", "눈", "바람", "햇살", "달빛", "별빛", "안개", "구름",
    "바다", "산", "숲", "강", "꽃", "낙엽", "침묵", "고요",
    # 삶·철학
    "시간", "기억", "현재", "순간", "여행", "길", "집", "뿌리",
    "지혜", "평화", "창의", "열정", "목적", "소명", "운명", "선택",
    "행복", "만족", "풍요", "단순", "진심", "진정성", "본질", "깊이",
]

VISUAL_STYLES = [
    "photoreal",
    "watercolor",
    "ink",
    "oil_painting",
    "pencil_sketch",
    "photography",
]

CONTENT_TONES = [
    "따뜻하고 포근한",
    "잔잔하고 서정적인",
    "깊고 사색적인",
    "맑고 희망찬",
    "우아하고 고요한",
    "감동적이고 진지한",
    "섬세하고 감성적인",
]

_NO_TEXT = (
    "Do not invent any background text or symbols. No inaccurate Korean, no pseudo-letters, "
    "no unreadable glyph-like marks, no decorative writing strokes, no signage, "
    "no watermark, no stamp, no label, no caption. Pure image only."
)
_NO_COLLAGE = (
    "Single unified scene — no collage, no double exposure, no montage, "
    "no multiple overlapping images, no split frame, no image-within-image."
)
_LAYOUT = (
    "LAYOUT ZONES (strict): "
    "① TOP-LEFT corner (left 55%, top 14% of frame) kept plain and empty — author name overlay goes here. "
    "② BOTTOM 38% of frame kept plain, calm, and free of all detail — subtitle text overlay goes here. "
    "③ CENTER and upper-right carry the main visual subject and atmosphere."
)

_STYLE_PREFIX: dict[str, str] = {
    "photoreal": f"photorealistic DSLR photography, 8K resolution, physically accurate lighting, sharp focus, single coherent scene, cinematic color grading, award-winning landscape photography quality. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
    "watercolor": f"beautiful watercolor painting, soft color washes, delicate brushstrokes, paper texture, single unified composition. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
    "ink": f"traditional East Asian ink painting, sumi-e style, minimal, flowing brushwork, generous empty space, single unified composition. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
    "oil_painting": f"impressionist oil painting, rich impasto texture, vivid brushstrokes, museum quality, single unified scene. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
    "pencil_sketch": f"detailed pencil sketch, fine linework, crosshatching, monochrome, single unified scene. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
    "photography": f"professional photography, natural light, photojournalistic, shallow depth of field, single coherent scene. {_NO_COLLAGE} {_NO_TEXT} {_LAYOUT}",
}


@dataclass
class EssayPackage:
    script: EssayScript
    background_path: Path
    bgm_signature: str


def build_essay_package(
    state_file: Path,
    output_dir: Path,
    openai_api_key: str,
    text_model: str,
    image_model: str,
    gemini_api_key: str,
    context: DailyContext,
    variation_seed: str = "",
) -> EssayPackage:
    state = load_state(state_file)
    topic = _pick_topic(state=state, date_iso=context.date_iso, variation_seed=variation_seed)
    visual_style = _pick_visual_style(state=state, date_iso=context.date_iso, variation_seed=variation_seed)

    tone = _pick_tone(date_iso=context.date_iso, variation_seed=variation_seed)
    try:
        script = _generate_essay(
            topic=topic,
            tone=tone,
            visual_style=visual_style,
            context=context,
            openai_api_key=openai_api_key,
            text_model=text_model,
            variation_seed=variation_seed,
        )
    except Exception as exc:
        print(f"[text] OpenAI essay generation failed; trying Gemini fallback: {exc}")
        try:
            script = _generate_essay_with_gemini(
                topic=topic,
                tone=tone,
                visual_style=visual_style,
                context=context,
                gemini_api_key=gemini_api_key,
                variation_seed=variation_seed,
            )
        except Exception as gemini_exc:
            print(f"[text] Gemini essay generation failed; using local fallback: {gemini_exc}")
            script = _build_local_fallback_essay(
                topic=topic,
                tone=tone,
                visual_style=visual_style,
                context=context,
                variation_seed=variation_seed,
            )

    background_path = _generate_background(
        script=script,
        output_dir=output_dir,
        gemini_api_key=gemini_api_key,
        image_model=image_model,
        date_iso=context.date_iso,
        variation_seed=variation_seed,
        openai_api_key=openai_api_key,
    )

    sig_base = f"{context.date_iso}_{topic[:8]}{variation_seed[:6]}"
    bgm_signature = sig_base[:20].replace(" ", "_")

    return EssayPackage(script=script, background_path=background_path, bgm_signature=bgm_signature)


def _build_local_fallback_essay(
    topic: str,
    tone: str,
    visual_style: str,
    context: DailyContext,
    variation_seed: str,
) -> EssayScript:
    seeded = random.Random(f"{context.date_iso}|fallback|{topic}|{tone}|{variation_seed}")
    openings = [
        f"{topic}은 하루의 가장 작은 틈에서 먼저 마음을 두드린다",
        f"오늘의 {topic}은 큰 결심보다 조용한 한 걸음에서 시작된다",
        f"{topic}을 오래 바라보면 마음은 서두르던 방향을 다시 고른다",
    ]
    middles = [
        f"{context.season_ko}의 공기 속에서 우리는 지나간 마음을 천천히 정리한다",
        f"{context.weather_summary_ko}라는 배경은 익숙한 생각에도 새 빛을 얹어 준다",
        "말보다 오래 남는 것은 결국 오늘을 견딘 태도와 작은 선택이다",
        "흔들림을 없애려 애쓰기보다 흔들리는 나를 끝까지 데리고 간다",
    ]
    closings = [
        f"그래서 오늘의 {topic}은 멀리 있는 답보다 곁의 순간을 붙드는 일이다",
        "마음이 조금 느려질 때, 삶은 다시 알아들을 수 있는 목소리로 온다",
        "작은 문장을 오래 품으면 하루의 표정도 조금은 다르게 열린다",
    ]
    lines = [seeded.choice(openings), *seeded.sample(middles, k=3), seeded.choice(closings)]
    image_prompt_en = (
        f"{context.season_ko} morning atmosphere in Seoul, {topic} theme, "
        f"{visual_style} style, quiet natural light, no people, calm empty lower frame"
    )
    bgm_prompt_en = (
        f"{tone} Korean inspirational short background music, soft piano, "
        "warm ambient texture, no vocals, gentle pacing"
    )
    title = f"{topic}을 붙드는 아침 #Shorts"
    description = f"{lines[0]}\n\n#Shorts #쇼츠 #에세이 #감성 #아침"
    return EssayScript(
        topic=topic,
        lines=lines,
        author_line="gikim",
        source_line="gikim",
        is_original=True,
        visual_style=visual_style,
        image_prompt_en=image_prompt_en,
        bgm_prompt_en=bgm_prompt_en,
        bgm_mood="reflective",
        mood="calm",
        title=title[:100],
        description=description,
        tags=["에세이", "감성", topic, visual_style],
    )


def _pick_topic(state: dict, date_iso: str, variation_seed: str) -> str:
    recent = state.get("recent_topics", [])[-10:]
    candidates = [t for t in ESSAY_TOPICS if t not in recent]
    seeded = random.Random(f"{date_iso}|topic|{variation_seed}")
    return seeded.choice(candidates or ESSAY_TOPICS)


def _pick_tone(date_iso: str, variation_seed: str) -> str:
    seeded = random.Random(f"{date_iso}|tone|{variation_seed}")
    return seeded.choice(CONTENT_TONES)


def _pick_visual_style(state: dict, date_iso: str, variation_seed: str) -> str:
    recent = state.get("recent_visual_styles", [])[-3:]
    candidates = [s for s in VISUAL_STYLES if s not in recent]
    seeded = random.Random(f"{date_iso}|style|{variation_seed}")
    return seeded.choice(candidates or VISUAL_STYLES)


def _generate_essay(
    topic: str,
    tone: str,
    visual_style: str,
    context: DailyContext,
    openai_api_key: str,
    text_model: str,
    variation_seed: str,
) -> EssayScript:
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    system_prompt, user_prompt = _essay_prompts(topic, tone, visual_style, context, variation_seed)

    response = client.chat.completions.create(
        model=text_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.92,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    return _essay_script_from_data(json.loads(raw), topic, visual_style)


def _generate_essay_with_gemini(
    topic: str,
    tone: str,
    visual_style: str,
    context: DailyContext,
    gemini_api_key: str,
    variation_seed: str,
) -> EssayScript:
    if not gemini_api_key:
        raise RuntimeError("Gemini API key is not configured.")
    from google import genai
    from google.genai import types

    system_prompt, user_prompt = _essay_prompts(topic, tone, visual_style, context, variation_seed)
    client = genai.Client(api_key=gemini_api_key)
    model = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model,
        contents=f"{system_prompt}\n\n{user_prompt}",
        config=types.GenerateContentConfig(
            temperature=0.92,
            response_mime_type="application/json",
        ),
    )
    raw = response.text or "{}"
    return _essay_script_from_data(json.loads(raw), topic, visual_style)


def _essay_prompts(
    topic: str,
    tone: str,
    visual_style: str,
    context: DailyContext,
    variation_seed: str,
) -> tuple[str, str]:
    system_prompt = (
        "당신은 깊이 있는 감성과 문학적 언어를 가진 한국어 에세이 작가입니다.\n"
        "매일 아침 유튜브 숏츠용 짧은 에세이 또는 좋은 글귀를 작성합니다.\n"
        "글은 화면에 5~6개의 구절로 나뉘어 순차적으로 표시되며 여성 아나운서가 낭독합니다.\n"
        "각 구절은 귀로 들었을 때 의미가 자연스럽게 전달되어야 하고,\n"
        "시적인 여운과 구체적인 이미지가 살아있는 언어로 써야 합니다.\n"
        "진부한 표현, 뻔한 격언, 단순 나열은 피하고 독자의 마음을 건드리는 문장을 씁니다.\n"
        "반드시 JSON만 출력하세요. 마크다운 코드블록 없이 순수 JSON으로만 응답합니다."
    )

    seed_note = f"\n(변주 시드: {variation_seed[:8]})" if variation_seed else ""
    user_prompt = (
        f"오늘의 창작 조건:\n"
        f"- 날짜: {context.date_iso} ({context.weekday_name_ko})\n"
        f"- 계절: {context.season_ko}\n"
        f"- 날씨 공기감: {context.weather_summary_ko}\n"
        f"- 주제: {topic}\n"
        f"- 글의 톤: {tone}\n"
        f"- 이미지 스타일: {visual_style}{seed_note}\n\n"
        "창작 요구사항:\n"
        "1. 주제를 정면으로 다루되, 예상치 못한 각도·비유·장면으로 풀어낼 것.\n"
        "2. 구절 수: 5개 또는 6개 (내용 흐름에 맞게 선택). 각 구절은 30~55자.\n"
        "3. 각 구절은 독립된 한 문장으로 의미가 완결되어야 함 — 나레이션으로 들었을 때 끊김 없이 자연스럽게.\n"
        "4. 첫 구절은 시청자의 시선을 끌어당기는 인상적인 문장으로 시작할 것.\n"
        "5. 마지막 구절은 여운이 남는 마무리로 끝낼 것.\n"
        "6. 기존 문학·시·노래 문구를 인용한 경우: is_original=false, author=저자명, source=작품명.\n"
        "7. 완전 창작인 경우: is_original=true, author='gikim', source='gikim'.\n"
        "8. 배경 이미지 프롬프트: 구체적인 장소·빛·계절·질감을 묘사, 사람 없이, 영어로.\n"
        "9. BGM 프롬프트: 악기·리듬·분위기를 구체적으로 묘사, 영어로.\n\n"
        "다음 JSON 형식으로만 응답하세요:\n"
        "{\n"
        '  "topic": "에세이 주제",\n'
        '  "lines": ["구절1", "구절2", ..., "구절5 또는 6"],\n'
        '  "is_original": true,\n'
        '  "author": "gikim",\n'
        '  "source": "gikim",\n'
        '  "mood": "calm",\n'
        '  "bgm_mood": "reflective",\n'
        '  "title": "유튜브 제목 (25자 이내, 해시태그 제외)",\n'
        '  "description": "에세이 핵심 내용 요약 (90자 이내, 첫 구절 포함 권장)",\n'
        '  "tags": ["에세이", "감성", "좋은글귀"],\n'
        '  "image_prompt_en": "구체적 배경 이미지 프롬프트 (장소·빛·계절·질감, 영어, 사람 없이)",\n'
        '  "bgm_prompt_en": "구체적 BGM 프롬프트 (악기·리듬·분위기, 영어)"\n'
        "}\n"
        "bgm_mood 옵션: meditative, reflective, focused\n"
        "mood 옵션: calm, hopeful, melancholic, peaceful, energetic, tender"
    )
    return system_prompt, user_prompt


def _essay_script_from_data(data: dict, topic: str, visual_style: str) -> EssayScript:
    lines = data.get("lines", [])
    if not (5 <= len(lines) <= 6):
        lines = (lines + [""] * 6)[:6] if len(lines) < 5 else lines[:6]

    is_original = bool(data.get("is_original", True))
    author = data.get("author", "gikim")
    source = data.get("source", "gikim")
    author_line = f"✍ {author}" if is_original else f"📖 {author}"
    source_line = source if is_original else f"출처: {source}"

    title_raw = data.get("title", f"{topic}에 대하여")
    title = title_raw if "#shorts" in title_raw.lower() else f"{title_raw} #Shorts"

    description = data.get("description", "\n".join(lines[:2]))
    tags = data.get("tags", ["에세이", "감성", topic])
    if "에세이" not in tags:
        tags.insert(0, "에세이")

    image_prompt_en = data.get("image_prompt_en", f"{topic} mood, {visual_style} art style, no people, serene")
    bgm_prompt_en = data.get("bgm_prompt_en", f"gentle ambient music matching {topic} theme, no bass")
    bgm_mood = data.get("bgm_mood", "reflective")
    if bgm_mood not in ("meditative", "reflective", "focused"):
        bgm_mood = "reflective"
    mood = data.get("mood", "calm")
    if mood not in ("calm", "hopeful", "melancholic", "peaceful", "energetic", "tender"):
        mood = "calm"

    shorts_hashtags = "#Shorts #쇼츠 #에세이 #감성 #아침"
    full_description = f"{description}\n\n{shorts_hashtags}"

    return EssayScript(
        topic=topic,
        lines=lines,
        author_line=author_line,
        source_line=source_line,
        is_original=is_original,
        visual_style=visual_style,
        image_prompt_en=image_prompt_en,
        bgm_prompt_en=bgm_prompt_en,
        bgm_mood=bgm_mood,
        mood=mood,
        title=title[:100],
        description=full_description,
        tags=tags,
    )


def _dalle3_prompt(style_prefix: str, scene: str, topic: str) -> str:
    return (
        f"Background image for a Korean inspirational essay short video. "
        f"Style: {style_prefix}. Scene: {scene}. Topic: {topic}. "
        "IMPORTANT: Do not invent any background text, signs, watermarks, writing, "
        "fake letters, unreadable Korean-like marks, glyph-like marks, or calligraphy in the image. "
        "Korean title/subtitle text will be rendered later by the video pipeline, not inside the background image. "
        "The bottom 40% of the image must be kept very calm, simple, and empty "
        "(reserved for subtitle text overlay — no objects, no detail). "
        "The top-left area must be plain and uncluttered "
        "(reserved for author credit overlay). "
        "Single unified scene only — no collage, no montage. "
        "No people, no faces, no anime characters. "
        "Vertical 9:16 portrait orientation."
    )


TARGET_RESOLUTION = (1080, 1920)  # 9:16 세로 쇼츠


def _normalize_to_9_16(image_path: Path, target: tuple[int, int] = TARGET_RESOLUTION) -> None:
    """생성된 배경 이미지를 정확한 9:16(1080x1920) 프레임으로 맞춘다.

    GPT Image portrait output uses 1024x1536 and DALL-E 3 uses 1024x1792;
    Imagen can still return slightly different dimensions by model, so this
    enforces the final frame.
    이렇게 하면 저장되는 배경 자체가 9:16이 되어 렌더 단계의 추가 크롭이
    예측 가능해지고, 배경 비율이 9:16이 아닌 문제를 방지한다.
    """
    try:
        from PIL import Image, ImageOps

        with Image.open(image_path) as im:
            im = im.convert("RGB")
            fitted = ImageOps.fit(im, target, method=Image.LANCZOS, centering=(0.5, 0.5))
            fitted.save(image_path)
    except Exception as exc:  # 정규화 실패 시 원본을 그대로 두고 렌더 단계 크롭에 위임
        print(f"[image] 9:16 정규화 실패(원본 유지): {exc}")


def _try_openai_image(prompt: str, output_path: Path, openai_api_key: str) -> str | None:
    if not openai_api_key:
        return None
    import base64
    import urllib.request
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    preferred_model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
    quality = os.environ.get("OPENAI_IMAGE_QUALITY", "low")
    ordered_models = [preferred_model, "gpt-image-1", "gpt-image-1-mini", "dall-e-3", "dall-e-2"]
    candidates: list[tuple[str, dict[str, str]]] = []
    for model in ordered_models:
        if any(existing == model for existing, _ in candidates):
            continue
        if model.startswith("gpt-image-"):
            candidates.append((model, {"size": "1024x1536", "quality": quality}))
        elif model == "dall-e-3":
            candidates.append((model, {"size": "1024x1792", "quality": "hd"}))
        elif model == "dall-e-2":
            candidates.append((model, {"size": "1024x1024"}))
        else:
            candidates.append((model, {"size": "1024x1536", "quality": quality}))

    for model, params in candidates:
        try:
            resp = client.images.generate(model=model, prompt=prompt, n=1, **params)
            image_data = resp.data[0]
            b64_json = getattr(image_data, "b64_json", None)
            if b64_json:
                image_bytes = base64.b64decode(b64_json)
            else:
                image_url = getattr(image_data, "url", None)
                if not image_url:
                    raise ValueError("이미지 응답에 b64_json/url이 없습니다.")
                with urllib.request.urlopen(image_url, timeout=60) as response:
                    image_bytes = response.read()
            output_path.write_bytes(image_bytes)
            _normalize_to_9_16(output_path)
            return model
        except Exception as exc:
            print(f"[image] OpenAI 이미지 모델 실패 ({model}): {exc}")
    return None


def _generate_background(
    script: EssayScript,
    output_dir: Path,
    gemini_api_key: str,
    image_model: str,
    date_iso: str,
    variation_seed: str,
    openai_api_key: str = "",
) -> Path:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("`google-genai` 패키지가 필요합니다.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    sig = f"{date_iso}_{script.topic[:6]}{variation_seed[:4]}".replace(" ", "_")
    output_path = output_dir / f"{sig}_bg.png"

    style_prefix = _STYLE_PREFIX.get(script.visual_style, "artistic, no text")

    # ── 1차: OpenAI 이미지 모델 (GPT Image 우선, DALL-E는 fallback) ──
    openai_prompt = _dalle3_prompt(style_prefix, script.image_prompt_en, script.topic)
    openai_model = _try_openai_image(openai_prompt, output_path, openai_api_key)
    if openai_model:
        print(f"[image] OpenAI 배경 생성 완료 ({openai_model}): {output_path.name} / 주제: {script.topic}")
        return output_path

    # ── 2차 fallback: Imagen ──
    client = genai.Client(api_key=gemini_api_key)
    seed_suffix = f", variation {variation_seed[:6]}" if variation_seed else ""
    prompts = [
        f"{style_prefix}, {script.image_prompt_en}{seed_suffix}",
        f"{style_prefix}, {script.topic} theme, serene atmosphere, no people{seed_suffix}",
        f"{style_prefix}, abstract mood representing {script.mood}, beautiful composition{seed_suffix}",
    ]

    for attempt, prompt in enumerate(prompts):
        try:
            result = client.models.generate_images(
                model=image_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    person_generation="dont_allow",
                ),
            )
            images = getattr(result, "generated_images", None) or []
            if not images:
                raise ValueError("빈 결과")
            output_path.write_bytes(images[0].image.image_bytes)
            _normalize_to_9_16(output_path)
            print(f"[image] Imagen 배경 생성 완료 (시도 {attempt + 1}): {output_path.name} / 주제: {script.topic}")
            return output_path
        except Exception as exc:
            print(f"[image] Imagen 시도 {attempt + 1} 실패: {exc}")

    _generate_local_background(output_path, script.topic, script.mood, variation_seed)
    print(f"[image] API 배경 생성 실패 — 로컬 9:16 fallback 사용: {output_path.name} / 주제: {script.topic}")
    return output_path


def _generate_local_background(output_path: Path, topic: str, mood: str, variation_seed: str) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    width, height = TARGET_RESOLUTION
    palettes = {
        "calm": ((18, 35, 50), (212, 198, 172), (88, 120, 132)),
        "warm": ((54, 34, 40), (236, 176, 112), (112, 78, 68)),
        "clear": ((20, 48, 72), (180, 218, 224), (76, 112, 142)),
        "deep": ((20, 24, 36), (120, 104, 154), (58, 72, 96)),
    }
    palette_key = "warm" if mood in {"hopeful", "warm"} else "clear" if topic in {"새벽", "아침", "봄"} else "deep"
    top, bottom, accent = palettes.get(palette_key, palettes["calm"])
    image = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    seed = sum(ord(ch) for ch in f"{topic}|{mood}|{variation_seed}")
    for index in range(7):
        x = (seed * (index + 3) * 97) % width
        y = 180 + ((seed * (index + 5) * 53) % 900)
        radius = 160 + ((seed + index * 71) % 220)
        alpha = 28 + (index % 3) * 12
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(*accent, alpha),
        )
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    image = image.filter(ImageFilter.GaussianBlur(10))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    _normalize_to_9_16(output_path)
