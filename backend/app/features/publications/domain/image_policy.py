"""Imágenes aceptadas: se identifican por su contenido (magic bytes), nunca por la extensión."""

from app.shared.domain.result import AppError, Err, Ok, Result

MAX_IMAGE_BYTES = 5 * 1024 * 1024

MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


def sniff_image(data: bytes) -> str | None:
    """Extensión según la firma del fichero, o ``None`` si no es PNG/JPEG/GIF/WebP."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def validate_image(data: bytes, max_bytes: int = MAX_IMAGE_BYTES) -> Result[str]:
    if not data:
        return Err(AppError.invalid("La imagen está vacía"))
    if len(data) > max_bytes:
        return Err(AppError.too_large(f"La imagen supera el máximo de {max_bytes // (1024 * 1024)} MB"))
    ext = sniff_image(data)
    if ext is None:
        return Err(AppError.invalid("Formato de imagen no admitido (PNG, JPEG, GIF o WebP)"))
    return Ok(ext)
