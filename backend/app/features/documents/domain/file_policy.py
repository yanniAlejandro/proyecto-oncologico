"""Qué ficheros se aceptan en el repositorio y cuáles se pueden ver en el navegador.

Reglas puras: extensión en lista blanca + firma del contenido coherente con la
extensión (evita, p. ej., un HTML renombrado a .pdf), tamaño máximo y nombre saneado.
"""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.shared.domain.result import AppError, Err, Ok, Result


def _starts(*signatures: bytes) -> Callable[[bytes], bool]:
    return lambda data: any(data.startswith(sig) for sig in signatures)


def _is_text(data: bytes) -> bool:
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return b"\x00" not in data


_ZIP = _starts(b"PK\x03\x04")
_OLE = _starts(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # .doc/.xls/.ppt antiguos


@dataclass(frozen=True, slots=True)
class FileKind:
    extension: str
    media_type: str
    previewable: bool
    matches: Callable[[bytes], bool]

    @property
    def label(self) -> str:
        return self.extension.lstrip(".").upper()


_KINDS = [
    FileKind(".pdf", "application/pdf", True, _starts(b"%PDF-")),
    FileKind(".png", "image/png", True, _starts(b"\x89PNG\r\n\x1a\n")),
    FileKind(".jpg", "image/jpeg", True, _starts(b"\xff\xd8\xff")),
    FileKind(".jpeg", "image/jpeg", True, _starts(b"\xff\xd8\xff")),
    FileKind(".txt", "text/plain; charset=utf-8", True, _is_text),
    FileKind(".csv", "text/csv; charset=utf-8", False, _is_text),
    FileKind(".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", False, _ZIP),
    FileKind(".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", False, _ZIP),
    FileKind(".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", False, _ZIP),
    FileKind(".odt", "application/vnd.oasis.opendocument.text", False, _ZIP),
    FileKind(".ods", "application/vnd.oasis.opendocument.spreadsheet", False, _ZIP),
    FileKind(".doc", "application/msword", False, _OLE),
    FileKind(".xls", "application/vnd.ms-excel", False, _OLE),
]
KIND_BY_EXTENSION = {k.extension: k for k in _KINDS}
ALLOWED_EXTENSIONS = tuple(sorted(KIND_BY_EXTENSION))


def extension_of(filename: str) -> str:
    return PurePosixPath(filename.replace("\\", "/")).suffix.lower()


def kind_for(filename: str) -> FileKind | None:
    return KIND_BY_EXTENSION.get(extension_of(filename))


def sanitize_filename(filename: str, max_length: int = 150) -> str:
    """Solo el nombre base, sin rutas ni caracteres de control; conserva acentos."""
    name = PurePosixPath(filename.replace("\\", "/")).name
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r"[\x00-\x1f\x7f<>:\"/\\|?*]", "", name).strip(" .")
    if not name:
        return "documento"
    stem, ext = (name[: -len(e)], e) if (e := extension_of(name)) else (name, "")
    return stem[: max_length - len(ext)] + ext


def validate_upload(filename: str, data: bytes, max_bytes: int) -> Result[FileKind]:
    if not data:
        return Err(AppError.invalid("El archivo está vacío"))
    if len(data) > max_bytes:
        return Err(AppError.too_large(f"El archivo supera el máximo de {max_bytes // (1024 * 1024)} MB"))
    kind = kind_for(filename)
    if kind is None:
        allowed = ", ".join(e.lstrip(".").upper() for e in ALLOWED_EXTENSIONS)
        return Err(AppError.invalid(f"Tipo de archivo no permitido. Formatos aceptados: {allowed}"))
    if not kind.matches(data[:8192]):
        return Err(AppError.invalid(f"El contenido no corresponde a un archivo {kind.label}"))
    return Ok(kind)
