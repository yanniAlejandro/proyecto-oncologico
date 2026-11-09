from typing import Annotated

from fastapi import Depends

from app.shared.domain.storage import FileStorage
from app.shared.infrastructure.config import settings
from app.shared.infrastructure.local_storage import LocalFileStorage


def get_file_storage() -> FileStorage:
    return LocalFileStorage(settings.STORAGE_DIR)


Storage = Annotated[FileStorage, Depends(get_file_storage)]
