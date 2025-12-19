from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from src.monitor import BoardPost


def build_email_body(posts: Iterable[BoardPost], board_url: str) -> str:
    lines = []
    for post in posts:
        date_str = post.date.strftime("%Y-%m-%d %H:%M")
        lines.append(f"- {post.title} ({date_str})\n  {post.url}")
    return "새 게시글이 감지되었습니다:\n" + "\n".join(lines) + f"\n\n원본 게시판: {board_url}"


def send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    sender: str,
    recipient: str,
    posts: Iterable[BoardPost],
    board_url: str,
    use_tls: bool = True,
) -> None:
    message = EmailMessage()
    message["Subject"] = "[알림] 새로운 게시글이 감지되었습니다"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(build_email_body(posts, board_url))

    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(username, password)
            server.send_message(message)
