import contextlib
import os
import re
import tempfile
from pathlib import Path

# Las claves las genera el sistema (uuid hex + extensión); cualquier otra cosa se rechaza.
_KEY = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]{1,5}$")


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _resolve(self, key: str) -> Path:
        if not _KEY.fullmatch(key):
            raise ValueError(f"Clave de almacenamiento inválida: {key!r}")
        return self._root / key[:2] / key

    def save(self, key: str, data: bytes) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".upload-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(tmp, target)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def path(self, key: str) -> Path | None:
        try:
            target = self._resolve(key)
        except ValueError:
            return None
        return target if target.is_file() else None

    def delete(self, key: str) -> None:
        with contextlib.suppress(ValueError):
            self._resolve(key).unlink(missing_ok=True)
