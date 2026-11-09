"""Puerto de almacenamiento de ficheros (documentos, imágenes de publicaciones y de «Quiénes somos»)."""

from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def path(self, key: str) -> Path | None: ...
    def delete(self, key: str) -> None: ...
