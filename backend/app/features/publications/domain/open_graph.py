"""Lectura de etiquetas Open Graph (lo que usa WhatsApp para la vista previa). Puro: sin red."""

import contextlib
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin

from app.features.publications.domain.model import LinkPreview

MAX_TITLE = 500
MAX_DESCRIPTION = 1000


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower().strip()
            if key and "content" in a and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def _clean(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    text = " ".join(unescape(value).split())
    return text[:limit] or None


def parse_open_graph(html: str, page_url: str) -> LinkPreview:
    parser = _MetaParser()
    with contextlib.suppress(Exception):  # HTML roto: nos quedamos con lo que se haya leído
        parser.feed(html)
    m = parser.meta
    image = m.get("og:image") or m.get("og:image:url") or m.get("twitter:image")
    image_url = urljoin(page_url, image) if image else None
    if image_url and not image_url.startswith(("http://", "https://")):
        image_url = None
    return LinkPreview(
        url=page_url,
        title=_clean(m.get("og:title") or m.get("twitter:title") or parser.title, MAX_TITLE),
        description=_clean(
            m.get("og:description") or m.get("twitter:description") or m.get("description"), MAX_DESCRIPTION
        ),
        image_url=image_url,
        site_name=_clean(m.get("og:site_name"), 200),
    )
