"""Descarga de páginas e imágenes de Internet para la vista previa, con protección SSRF.

Quien tenga el permiso «publicaciones» puede hacer que el servidor pida una URL. Sin
protección, podría usarlo para llegar a equipos internos de la red del hospital. Por eso:
  · solo http/https y puertos 80/443;
  · el host se resuelve y TODAS sus IP deben ser públicas (se rechazan privadas, loopback,
    link-local, multicast y reservadas), también en cada redirección (máx. 3);
  · tiempo límite y tamaño máximo; la imagen se valida después por su contenido.
Limitación conocida: entre la comprobación DNS y la conexión hay una ventana (DNS rebinding).
"""

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from urllib.parse import urljoin, urlparse

import httpx

from app.features.publications.domain.image_policy import MAX_IMAGE_BYTES
from app.features.publications.domain.model import LinkPreview
from app.features.publications.domain.open_graph import parse_open_graph

MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 5.0
USER_AGENT = "PortalOncologicoHOLH/1.0 (vista previa de enlaces)"

Resolver = Callable[[str, int], Awaitable[list[str]]]


async def system_resolver(host: str, port: int) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return [str(info[4][0]) for info in infos]


def is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


class HttpLinkPreviewer:
    def __init__(
        self,
        *,
        resolver: Resolver = system_resolver,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self._resolve = resolver
        self._transport = transport
        self._timeout = timeout

    async def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError:
            return False
        if port not in (80, 443):
            return False
        try:
            addresses = await self._resolve(parsed.hostname, port)
        except OSError:
            return False
        return bool(addresses) and all(is_public_ip(a) for a in addresses)

    async def _get(self, url: str, *, max_bytes: int, truncate: bool, accept: str) -> tuple[bytes, str, str] | None:
        """(cuerpo, content-type, url final) o ``None``. ``truncate``: cortar en vez de fallar si es grande."""
        current = url
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                follow_redirects=False,
                timeout=self._timeout,
                headers={"User-Agent": USER_AGENT, "Accept": accept},
            ) as client:
                for _ in range(MAX_REDIRECTS + 1):
                    if not await self._is_allowed(current):
                        return None
                    async with client.stream("GET", current) as response:
                        if response.is_redirect and "location" in response.headers:
                            current = urljoin(current, response.headers["location"])
                            continue
                        if response.status_code != 200:
                            return None
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > max_bytes:
                                if not truncate:
                                    return None
                                del body[max_bytes:]
                                break
                        return bytes(body), response.headers.get("content-type", ""), current
        except (httpx.HTTPError, OSError, ValueError):
            return None
        return None  # demasiadas redirecciones

    async def preview(self, url: str) -> LinkPreview | None:
        got = await self._get(url, max_bytes=MAX_HTML_BYTES, truncate=True, accept="text/html,application/xhtml+xml")
        if got is None:
            return None
        body, content_type, final_url = got
        if "html" not in content_type.lower():
            return None
        charset = "utf-8"
        if "charset=" in content_type.lower():
            charset = content_type.lower().split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
        try:
            html = body.decode(charset, errors="replace")
        except LookupError:
            html = body.decode("utf-8", errors="replace")
        preview = parse_open_graph(html, final_url)
        return LinkPreview(
            url=url,
            title=preview.title,
            description=preview.description,
            image_url=preview.image_url,
            site_name=preview.site_name,
        )

    async def fetch_image(self, url: str) -> bytes | None:
        got = await self._get(url, max_bytes=MAX_IMAGE_BYTES, truncate=False, accept="image/*")
        return got[0] if got else None
