from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from src.monitor import BoardPost


class SQLiteState:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    first_seen TIMESTAMP NOT NULL
                )
                """
            )

    def seen_ids(self) -> set[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id FROM posts").fetchall()
        return {row[0] for row in rows}

    def filter_new(self, posts: Sequence[BoardPost]) -> list[BoardPost]:
        new_posts: list[BoardPost] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN")
            for post in posts:
                exists = conn.execute("SELECT 1 FROM posts WHERE id = ?", (post.id,)).fetchone()
                if exists:
                    continue
                conn.execute(
                    "INSERT INTO posts(id, first_seen) VALUES(?, ?)",
                    (post.id, datetime.utcnow().isoformat()),
                )
                new_posts.append(post)
            conn.commit()
        return new_posts

    def hydrate(self, posts: Iterable[BoardPost]) -> list[BoardPost]:
        return self.filter_new(list(posts))
