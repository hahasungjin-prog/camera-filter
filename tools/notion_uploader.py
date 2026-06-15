"""
사진 분석 결과를 Notion 데이터베이스에 저장한다.
입력: .tmp/analysis.json (또는 dict 직접 전달)
"""

import json
import os
import requests
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def load_analysis():
    path = ".tmp/analysis.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} 없음. photo_analyzer.py를 먼저 실행하세요.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _text(content):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": str(content)[:2000]}}]
        },
    }


def _heading(content, level=2):
    htype = f"heading_{level}"
    return {
        "object": "block",
        "type": htype,
        htype: {"rich_text": [{"type": "text", "text": {"content": content}}]},
    }


def _divider():
    return {"object": "block", "type": "divider", "divider": {}}


def _code(content):
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": str(content)[:2000]}}],
            "language": "plain text",
        },
    }


def _callout(content, emoji="💡"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": str(content)[:2000]}}],
            "icon": {"type": "emoji", "emoji": emoji},
        },
    }


def _upload_image(image_path: str) -> str | None:
    """이미지를 노션에 업로드하고 file_upload_id 반환. 실패 시 None."""
    try:
        ext = Path(image_path).suffix.lower()
        media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        content_type = media_types.get(ext, "image/jpeg")
        filename = Path(image_path).name

        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # 1. 업로드 세션 생성
        resp = requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers=headers,
            json={"filename": filename, "content_type": content_type},
        )
        resp.raise_for_status()
        data = resp.json()
        upload_url = data["upload_url"]
        file_upload_id = data["id"]

        # 2. 파일 업로드
        with open(image_path, "rb") as f:
            put_resp = requests.put(
                upload_url,
                headers={"Content-Type": content_type},
                data=f.read(),
            )
        put_resp.raise_for_status()
        return file_upload_id
    except Exception:
        return None


def _image_block(file_upload_id: str):
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
        },
    }


def _get_title_prop(notion):
    try:
        db = notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
        for name, val in (db.get("properties") or {}).items():
            if val.get("type") == "title":
                return name
    except Exception:
        pass
    return "Name"


def upload(analysis: dict = None, image_path: str = None) -> str:
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        raise ValueError(".env에 NOTION_TOKEN, NOTION_DATABASE_ID가 없습니다.")

    notion = Client(auth=NOTION_TOKEN)
    if analysis is None:
        analysis = load_analysis()

    today = str(date.today())
    source = analysis.get("source_image", "unknown")
    filter_name = analysis.get("filter_name", "")
    filter_desc = analysis.get("filter_desc", "")
    prompt_universal = analysis.get("prompt_universal", "")
    prompt_mj = analysis.get("prompt_midjourney", "")
    prompt_dalle = analysis.get("prompt_dalle", "")
    hook = analysis.get("hook_ko", "")
    cta = analysis.get("cta_ko", "")
    caption = analysis.get("caption_ko", "")

    page_title = f"[{today}] {source} - {filter_name}"

    # 이미지 블록 준비
    image_blocks = []
    if image_path and os.path.exists(image_path):
        file_upload_id = _upload_image(image_path)
        if file_upload_id:
            image_blocks = [_image_block(file_upload_id)]

    blocks = [
        _heading("📷 사진 정보", 2),
        *image_blocks,
        _text(f"원본 파일: {source}"),
        _text(f"선택 필터: {filter_name} ({filter_desc})"),
        _divider(),
        _heading("✨ AI 이미지 프롬프트", 2),
        _heading("범용 (Midjourney / DALL-E 모두)", 3),
        _code(prompt_universal),
        _heading("Midjourney 최적화", 3),
        _code(prompt_mj),
        _heading("DALL-E / ChatGPT 최적화", 3),
        _code(prompt_dalle),
        _divider(),
        _heading("📱 인스타그램 콘텐츠", 2),
        _callout(hook, "🪝"),
        _callout(cta, "📣"),
        _divider(),
        _heading("전체 캡션 초안", 3),
        _text(caption),
    ]

    title_prop = _get_title_prop(notion)
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={title_prop: {"title": [{"text": {"content": page_title}}]}},
        children=blocks,
    )
    return page_title


if __name__ == "__main__":
    title = upload()
    print(f"[notion_uploader] 완료: {title}")
