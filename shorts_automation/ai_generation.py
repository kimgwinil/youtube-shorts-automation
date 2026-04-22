from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha1
import json
from pathlib import Path
import random
from typing import Any, Dict, List

from openai import OpenAI

from .daily_context import DailyContext
from .script_builder import QuoteEntry, VideoScript, _load_quotes
from .state_store import load_state, save_state


@dataclass
class DailyPackage:
    script: VideoScript
    background_path: Path
    bgm_signature: str


def build_daily_package(
    quotes_file: Path,
    state_file: Path,
    output_dir: Path,
    openai_api_key: str,
    text_model: str,
    image_model: str,
    context: DailyContext,
) -> DailyPackage:
    state = load_state(state_file)
    quote = _choose_quote(quotes_file, state, context)
    script = _generate_unique_script(quote, state, openai_api_key, text_model, context)
    background_path = _generate_background_image(script, output_dir, openai_api_key, image_model)
    bgm_signature = _music_signature(script, context)

    _append_unique(state, "used_quotes", quote.quote_id, 120)
    _append_unique(state, "recent_quote_ids", quote.quote_id, 20)
    _append_unique(state, "recent_titles", script.title, 20)
    _append_unique(state, "recent_image_fingerprints", _image_fingerprint(script), 20)
    _append_unique(state, "recent_music_signatures", bgm_signature, 20)
    _append_unique(state, "recent_dates", context.date_iso, 20)
    save_state(state_file, state)

    return DailyPackage(script=script, background_path=background_path, bgm_signature=bgm_signature)


def _generate_unique_script(
    quote: QuoteEntry,
    state: Dict[str, Any],
    api_key: str,
    text_model: str,
    context: DailyContext,
) -> VideoScript:
    recent_titles = set(state.get("recent_titles", [])[-12:])
    recent_fingerprints = set(state.get("recent_image_fingerprints", [])[-12:])
    avoid_note = ""
    script: VideoScript | None = None
    for attempt in range(4):
        script = _generate_script_with_ai(quote, state, api_key, text_model, context, avoid_note=avoid_note)
        if script.title not in recent_titles and _image_fingerprint(script) not in recent_fingerprints:
            return script
        avoid_note = (
            "이전 결과와 너무 비슷합니다. 제목 표현과 시각 묘사를 더 다르게 바꾸고, "
            "도입 문장과 마무리 문장도 전혀 다른 리듬으로 작성하세요."
        )
    if script is None:
        raise RuntimeError("AI 스크립트 생성에 실패했습니다.")
    return script


def _choose_quote(quotes_file: Path, state: Dict[str, Any], context: DailyContext) -> QuoteEntry:
    quotes = _load_quotes(quotes_file)
    recent_ids = set(state.get("recent_quote_ids", []))
    candidates = [quote for quote in quotes if quote.quote_id not in recent_ids]
    if not candidates:
        candidates = quotes

    mood_matched = [quote for quote in candidates if quote.mood == context.mood_hint]
    pool = mood_matched or candidates
    seeded = random.Random(f"{context.date_iso}|{context.weekday_name_ko}|{context.weather_summary_ko}")
    return seeded.choice(pool)


def _generate_script_with_ai(
    quote: QuoteEntry,
    state: Dict[str, Any],
    api_key: str,
    text_model: str,
    context: DailyContext,
    avoid_note: str = "",
) -> VideoScript:
    client = OpenAI(api_key=api_key)
    recent_titles = state.get("recent_titles", [])[-8:]
    prompt = f"""
너는 한국어 유튜브 쇼츠 작가다.
다음 고정 명언을 바탕으로 오늘 업로드할 한국어 쇼츠용 결과를 JSON으로만 출력하라.

오늘 정보:
- 날짜: {context.date_iso}
- 지역: {context.location_name}
- 요일: {context.weekday_name_ko}
- 계절: {context.season_ko}
- 날씨: {context.weather_summary_ko}
- 추천 분위기: {context.mood_hint}

고정 명언 정보:
- author: {quote.author}
- source: {quote.source}
- quote: {quote.quote}
- interpretation: {quote.interpretation}
- mood: {quote.mood}
- visual_style: {quote.visual_style}
- bgm_mood: {quote.bgm_mood}
- context: {quote.context}

최근 제목:
{json.dumps(recent_titles, ensure_ascii=False)}

규칙:
1. 명언 원문은 바꾸지 말 것.
2. lines는 6개 또는 7개.
3. 모든 문장은 한국어.
4. 첫 줄은 시선이 멈추는 도입.
5. 마지막 줄은 여운이 남는 마무리.
6. title은 최근 제목과 겹치지 않게.
7. visual_prompt는 오늘 날씨와 계절감이 드러나게.
8. JSON 외 다른 텍스트 금지.
9. 최근 결과와 비슷한 표현을 반복하지 말 것.

추가 지시:
{avoid_note or "없음"}

필수 JSON 스키마:
{{
  "title": "...",
  "description": "...",
  "tags": ["...", "..."],
  "lines": ["...", "..."],
  "author_line": "...",
  "source_line": "...",
  "visual_prompt": "...",
  "visual_style": "{quote.visual_style}",
  "bgm_mood": "{quote.bgm_mood}",
  "total_duration": 24.0
}}
"""
    response = client.chat.completions.create(
        model=text_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or ""
    parsed = json.loads(raw)
    return VideoScript(
        quote=quote,
        title=parsed["title"][:90],
        description=parsed["description"],
        tags=parsed["tags"],
        lines=parsed["lines"],
        author_line=parsed["author_line"],
        source_line=parsed["source_line"],
        visual_prompt=parsed["visual_prompt"],
        total_duration=float(parsed.get("total_duration", max(24.0, len(parsed["lines"]) * 3.8))),
    )


def _generate_background_image(
    script: VideoScript,
    output_dir: Path,
    api_key: str,
    image_model: str,
) -> Path:
    client = OpenAI(api_key=api_key)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"{sha1((script.title + script.visual_prompt).encode('utf-8')).hexdigest()[:12]}_bg.png"
    response = client.images.generate(
        model=image_model,
        prompt=script.visual_prompt,
        size="1024x1536",
        quality="high",
    )
    image_data = response.data[0].b64_json if response.data else None
    if not image_data:
        raise RuntimeError("배경 이미지 생성 결과가 비어 있습니다.")
    filename.write_bytes(base64.b64decode(image_data))
    return filename


def _music_signature(script: VideoScript, context: DailyContext) -> str:
    raw = f"{script.quote.author}|{script.quote.bgm_mood}|{context.date_iso}|{context.weather_summary_ko}"
    return sha1(raw.encode("utf-8")).hexdigest()[:12]


def _image_fingerprint(script: VideoScript) -> str:
    raw = f"{script.quote.quote_id}|{script.visual_prompt}|{script.title}"
    return sha1(raw.encode("utf-8")).hexdigest()[:16]


def _append_unique(state: Dict[str, Any], key: str, value: str, limit: int) -> None:
    items = [item for item in state.get(key, []) if item != value]
    items.append(value)
    state[key] = items[-limit:]
