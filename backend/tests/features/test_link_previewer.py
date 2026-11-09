"""Previsualizador HTTP con red simulada (httpx.MockTransport) y DNS simulado: protección SSRF."""

import httpx
import pytest

from app.features.publications.infrastructure.http_previewer import HttpLinkPreviewer, is_public_ip
from tests.fakes import PNG

PUBLIC = "93.184.216.34"
DNS = {
    "noticias.cu": [PUBLIC],
    "cdn.cu": [PUBLIC],
    "intranet.holh": ["10.0.0.5"],
    "mixto.cu": [PUBLIC, "127.0.0.1"],
    "redirige.cu": [PUBLIC],
}
HTML = b'<meta property="og:title" content="Nota"><meta property="og:image" content="https://cdn.cu/a.png">'


async def resolver(host: str, port: int) -> list[str]:
    if host in DNS:
        return DNS[host]
    if host.replace(".", "").isdigit() or ":" in host:
        return [host]
    raise OSError("NXDOMAIN")


def handler(request: httpx.Request) -> httpx.Response:
    hit.append(str(request.url))
    host, path = request.url.host, request.url.path
    if host == "noticias.cu" and path == "/grande":
        return httpx.Response(200, headers={"content-type": "text/html"}, content=HTML + b" " * (3 * 1024 * 1024))
    if host == "cdn.cu" and path == "/enorme.png":
        return httpx.Response(200, headers={"content-type": "image/png"}, content=PNG + b"0" * (6 * 1024 * 1024))
    if host == "noticias.cu" and path == "/pdf":
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF")
    if host == "noticias.cu":
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=HTML)
    if host == "cdn.cu":
        return httpx.Response(200, headers={"content-type": "image/png"}, content=PNG)
    if host == "redirige.cu" and path == "/interna":
        return httpx.Response(302, headers={"location": "http://intranet.holh/secreto"})
    if host == "redirige.cu":
        return httpx.Response(301, headers={"location": "https://noticias.cu/nota"})
    return httpx.Response(200, headers={"content-type": "text/html"}, content=b"<title>interno</title>")


hit: list[str] = []


@pytest.fixture
def previewer():
    hit.clear()
    return HttpLinkPreviewer(resolver=resolver, transport=httpx.MockTransport(handler))


async def test_reads_open_graph(previewer):
    p = await previewer.preview("https://noticias.cu/nota")
    assert p.title == "Nota" and p.image_url == "https://cdn.cu/a.png"
    assert await previewer.fetch_image("https://cdn.cu/a.png") == PNG


async def test_follows_public_redirects(previewer):
    p = await previewer.preview("https://redirige.cu/")
    assert p is not None and p.title == "Nota"


@pytest.mark.parametrize(
    "url",
    [
        "http://intranet.holh/admin",  # IP privada
        "http://127.0.0.1/",  # loopback
        "http://169.254.169.254/latest/meta-data",  # metadatos cloud (link-local)
        "http://[::1]/",
        "https://mixto.cu/",  # una IP pública y otra local → se rechaza
        "https://noticias.cu:8443/",  # puerto no estándar
        "file:///etc/passwd",
        "https://no-existe.cu/",
    ],
)
async def test_blocks_internal_targets_without_connecting(previewer, url):
    assert await previewer.preview(url) is None
    assert hit == []  # ni siquiera se intenta la conexión


async def test_blocks_redirect_into_internal_network(previewer):
    assert await previewer.preview("https://redirige.cu/interna") is None
    assert hit == ["https://redirige.cu/interna"]


async def test_size_and_type_limits(previewer):
    big = await previewer.preview("https://noticias.cu/grande")
    assert big is not None and big.title == "Nota"  # HTML grande: se trunca, el <head> basta
    assert await previewer.preview("https://noticias.cu/pdf") is None
    assert await previewer.fetch_image("https://cdn.cu/enorme.png") is None  # imagen > 5 MB: se descarta


@pytest.mark.parametrize(
    ("ip", "public"),
    [("8.8.8.8", True), ("10.1.2.3", False), ("192.168.1.1", False), ("::ffff:127.0.0.1", False), ("x", False)],
)
def test_is_public_ip(ip, public):
    assert is_public_ip(ip) is public
