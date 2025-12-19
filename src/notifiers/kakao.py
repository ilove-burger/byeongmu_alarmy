from __future__ import annotations

import json
from typing import Iterable

import requests

from src.monitor import BoardPost

KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def build_template(posts: Iterable[BoardPost], board_url: str) -> dict:
    lines = [f"• {post.title} ({post.url})" for post in posts]
    text = "새 게시글이 감지되었습니다:\n" + "\n".join(lines)
    return {
        "object_type": "text",
        "text": text,
        "link": {"web_url": board_url, "mobile_web_url": board_url},
        "button_title": "게시판 열기",
    }


def send_kakao_message(access_token: str, posts: Iterable[BoardPost], board_url: str) -> None:
    template_object = json.dumps(build_template(posts, board_url), ensure_ascii=False)
    response = requests.post(
        KAKAO_API_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": template_object},
        timeout=10,
    )
    response.raise_for_status()
