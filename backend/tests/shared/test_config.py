from pathlib import Path

from app.shared.infrastructure.config import BACKEND_ROOT, Settings


def test_storage_dir_relative_is_anchored_to_backend_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # arrancar desde otra carpeta no debe cambiar dónde se guarda
    assert Settings(STORAGE_DIR=Path("storage")).STORAGE_DIR == BACKEND_ROOT / "storage"
    assert (BACKEND_ROOT / "app" / "main.py").is_file()


def test_storage_dir_absolute_is_kept():
    absolute = Path("/srv/holh/documentos")
    configured = Settings(STORAGE_DIR=absolute).STORAGE_DIR
    assert configured == absolute
