from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    id: str
    title: str
    url: str
    date: datetime


class BoardMonitor:
    """Fetch and parse board posts using Requests + BeautifulSoup.

    The parser assumes a simple table/`<li>` structure with an `<a>` that points
    to the detail page. If your board uses a different structure, adjust the
    selectors in `_iter_rows` or extend `parse_row` accordingly.
    """

    def __init__(self, board_url: str, session: Optional[requests.Session] = None):
        self.board_url = board_url
        self.session = session or requests.Session()

    def fetch_posts(self) -> List[BoardPost]:
        response = self.session.get(self.board_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        posts: List[BoardPost] = []

        for row in self._iter_rows(soup):
            parsed = self.parse_row(row)
            if parsed:
                posts.append(parsed)

        return posts

    def _iter_rows(self, soup: BeautifulSoup) -> Iterable:
        rows = soup.select("table tbody tr")
        if rows:
            return rows
        return soup.select("ul li, ol li")

    def parse_row(self, row) -> Optional[BoardPost]:
        anchor = row.find("a")
        date_cell = row.find("time") or row.find("td", class_=self._date_class_hint(row))

        if not anchor:
            return None

        title = anchor.get_text(strip=True)
        url = urljoin(self.board_url, anchor.get("href") or "")
        post_id = self._extract_id(anchor, url)
        date_value = self._parse_date(date_cell.get_text(strip=True) if date_cell else None)

        return BoardPost(id=post_id, title=title, url=url, date=date_value)

    def _extract_id(self, anchor, url: str) -> str:
        if anchor.has_attr("data-id"):
            return str(anchor["data-id"])

        parsed = urlparse(url)
        query_id = self._extract_from_query(parsed.query)
        if query_id:
            return query_id

        path_segments = [segment for segment in parsed.path.split("/") if segment]
        if path_segments:
            return path_segments[-1]

        text = anchor.get_text(strip=True)
        return text or url

    def _extract_from_query(self, query: str) -> Optional[str]:
        params = parse_qs(query)
        for key in ("id", "postId", "articleId"):
            value = params.get(key)
            if value:
                return value[0]
        return None

    def _parse_date(self, raw_value: Optional[str]) -> datetime:
        if not raw_value:
            return datetime.now()

        normalized = raw_value.replace(".", "-").strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        return datetime.now()

    def _date_class_hint(self, row) -> Optional[str]:
        date_classes = ["date", "regdate", "created"]
        for cls in date_classes:
            if row.find("td", class_=cls):
                return cls
        return None
