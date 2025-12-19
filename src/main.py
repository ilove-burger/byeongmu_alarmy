from __future__ import annotations

import logging
import os
import time
from typing import Iterable

import schedule
from dotenv import load_dotenv

from src.monitor import BoardMonitor, BoardPost
from src.notifiers.email import send_email
from src.notifiers.kakao import send_kakao_message
from src.state import SQLiteState

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def filter_posts(posts: Iterable[BoardPost], keyword: str) -> list[BoardPost]:
    lowered = keyword.lower()
    return [post for post in posts if lowered in post.title.lower()]


def run_cycle() -> None:
    board_url = os.environ.get("BOARD_URL")
    if not board_url:
        logger.error("BOARD_URL 환경 변수가 설정되지 않았습니다.")
        return

    keyword = os.environ.get("FILTER_KEYWORD", "사회복무요원")
    kakao_token = os.environ.get("KAKAO_ACCESS_TOKEN")
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    email_from = os.environ.get("EMAIL_FROM", "")
    email_to = os.environ.get("EMAIL_TO", "")
    state_path = os.environ.get("STATE_DB_PATH", "state.db")

    monitor = BoardMonitor(board_url)
    state = SQLiteState(state_path)

    posts = monitor.fetch_posts()
    filtered = filter_posts(posts, keyword)
    new_posts = state.filter_new(filtered)

    if not new_posts:
        logger.info("신규 게시글이 없습니다.")
        return

    logger.info("%d개의 신규 게시글 발견", len(new_posts))

    if kakao_token:
        try:
            send_kakao_message(kakao_token, new_posts, board_url)
            logger.info("카카오 알림 전송 완료")
        except Exception as exc:  # noqa: BLE001
            logger.exception("카카오 알림 전송 실패: %s", exc)

    if smtp_host and email_from and email_to and smtp_user and smtp_password:
        try:
            send_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                sender=email_from,
                recipient=email_to,
                posts=new_posts,
                board_url=board_url,
            )
            logger.info("이메일 알림 전송 완료")
        except Exception as exc:  # noqa: BLE001
            logger.exception("이메일 알림 전송 실패: %s", exc)


if __name__ == "__main__":
    load_dotenv()
    poll_interval = int(os.environ.get("POLL_INTERVAL_MINUTES", "5"))

    schedule.every(poll_interval).minutes.do(run_cycle)
    logger.info("모니터링 시작: %s 분 주기", poll_interval)
    while True:
        schedule.run_pending()
        time.sleep(1)
