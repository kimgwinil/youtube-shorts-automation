from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .ai_generation import build_daily_package
from .daily_context import build_daily_context
from .config import load_config
from .render import render_short
from .script_builder import build_script, pick_next_quote
from .state_store import load_state, save_state
from .upload import upload_video


def run_pipeline(project_root: Path, dry_run: bool = False, force: bool = False) -> dict:
    config = load_config(project_root)
    background_override = None
    bgm_override = None

    today = datetime.now(ZoneInfo(config.timezone_name)).strftime("%Y-%m-%d")
    state = load_state(config.state_file)
    if not force and not dry_run and today in state.get("recent_dates", []):
        return {"skipped": True, "reason": f"이미 오늘({today}) 영상이 업로드되었습니다. --force로 강제 실행 가능."}

    if config.enable_ai_generation and config.openai_api_key:
        context = build_daily_context(
            timezone_name=config.timezone_name,
            location_name=config.location_name,
            latitude=config.location_latitude,
            longitude=config.location_longitude,
        )
        package = build_daily_package(
            quotes_file=config.quotes_file,
            state_file=config.state_file,
            output_dir=config.output_dir,
            openai_api_key=config.openai_api_key,
            text_model=config.openai_text_model,
            image_model=config.openai_image_model,
            context=context,
        )
        script = package.script
        background_override = package.background_path
    else:
        quote = pick_next_quote(config.quotes_file, config.state_file)
        script = build_script(quote)

    render_result = render_short(
        script=script,
        background_dir=config.background_dir,
        output_dir=config.output_dir,
        font_file=config.font_file,
        shorts_hashtags=config.shorts_hashtags,
        background_override=background_override,
        bgm_override=bgm_override,
    )
    if dry_run:
        return {
            "video_path": str(render_result.video_path),
            "metadata_path": str(render_result.metadata_path),
            "youtube_video_id": None,
            "uploaded": False,
        }
    upload_result = upload_video(
        video_path=render_result.video_path,
        metadata_path=render_result.metadata_path,
        client_secrets_file=config.youtube_client_secrets_file,
        token_file=config.youtube_token_file,
        visibility=config.default_visibility,
        category_id=config.default_category_id,
    )
    current_state = load_state(config.state_file)
    dates = [d for d in current_state.get("recent_dates", []) if d != today]
    dates.append(today)
    current_state["recent_dates"] = dates[-20:]
    save_state(config.state_file, current_state)
    return {
        "video_path": str(render_result.video_path),
        "metadata_path": str(render_result.metadata_path),
        "youtube_video_id": upload_result["id"],
        "uploaded": True,
    }
