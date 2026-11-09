from uuid import uuid4

import pytest

from app.features.documents.application import use_cases as uc
from app.features.documents.domain.file_policy import kind_for, sanitize_filename, validate_upload
from app.features.documents.domain.model import Disposition
from app.shared.domain.result import ErrorKind
from app.shared.infrastructure.local_storage import LocalFileStorage
from tests.fakes import ADMIN, DOCTOR, EDITOR, FakeDocuments, FakeStorage
from tests.helpers import err, ok

PDF = b"%PDF-1.4\n contenido"
DOCX = b"PK\x03\x04 resto del zip"
MB = 1024 * 1024


# ---------- política de ficheros (dominio puro) ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd.pdf", "passwd.pdf"),
        ("C:\\Users\\x\\Informe final.docx", "Informe final.docx"),
        ("  .oculto.pdf. ", "oculto.pdf"),
        ("a<b>c:d|e?.pdf", "abcde.pdf"),
        ("Guía de mamá.pdf", "Guía de mamá.pdf"),
        ("", "documento"),
        ("x" * 300 + ".pdf", "x" * 146 + ".pdf"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_validate_upload_accepts_matching_signature():
    assert ok(validate_upload("a.pdf", PDF, MB)).media_type == "application/pdf"
    assert ok(validate_upload("a.DOCX", DOCX, MB)).label == "DOCX"
    assert ok(validate_upload("notas.txt", "texto con ñ".encode(), MB)).previewable


@pytest.mark.parametrize(
    ("name", "data", "kind"),
    [
        ("a.pdf", b"", ErrorKind.INVALID),
        ("a.exe", b"MZ....", ErrorKind.INVALID),
        ("a.html", b"<html>", ErrorKind.INVALID),
        ("falso.pdf", b"<html><script>", ErrorKind.INVALID),
        ("falso.docx", PDF, ErrorKind.INVALID),
        ("bin.txt", b"\x00\x01\x02", ErrorKind.INVALID),
        ("grande.pdf", PDF + b"x" * MB, ErrorKind.TOO_LARGE),
    ],
)
def test_validate_upload_rejects(name, data, kind):
    err(validate_upload(name, data, MB), kind)


def test_only_safe_types_are_previewable():
    assert kind_for("a.pdf").previewable and kind_for("a.png").previewable
    assert not kind_for("a.docx").previewable and not kind_for("a.csv").previewable
    assert kind_for("a.svg") is None  # SVG puede llevar scripts: no se acepta


# ---------- casos de uso ----------


@pytest.fixture
def repo():
    return FakeDocuments()


@pytest.fixture
def storage(tmp_path):
    return FakeStorage(tmp_path)


def upload(repo, storage, actor=EDITOR, filename="informe.pdf", data=PDF, max_bytes=MB):
    return uc.UploadDocument(repo, storage, max_bytes)(
        actor, title=" Informe ", description="  ", filename=filename, data=data
    )


async def test_manager_uploads_and_file_is_stored(repo, storage):
    doc = ok(await upload(repo, storage))
    assert doc.title == "Informe" and doc.description is None
    assert doc.file_type == "PDF" and doc.size_bytes == len(PDF)
    assert doc.is_previewable and doc.storage_key in storage.files
    assert doc.storage_key.endswith(".pdf") and "informe" not in doc.storage_key  # clave opaca


@pytest.mark.parametrize(("actor", "kind"), [(None, ErrorKind.UNAUTHENTICATED), (DOCTOR, ErrorKind.FORBIDDEN)])
async def test_upload_requires_manager_and_stores_nothing(repo, storage, actor, kind):
    err(await upload(repo, storage, actor=actor), kind)
    assert storage.files == {}


async def test_invalid_upload_stores_nothing(repo, storage):
    err(await upload(repo, storage, filename="x.pdf", data=b"<html>"), ErrorKind.INVALID)
    err(await upload(repo, storage, data=PDF * 10, max_bytes=20), ErrorKind.TOO_LARGE)
    assert storage.files == {} and repo.rows == {}


async def test_failed_db_insert_removes_orphan_file(repo, storage):
    repo.fail_on_add = True
    with pytest.raises(RuntimeError):
        await upload(repo, storage)
    assert storage.files == {}


async def test_external_link_documents(repo):
    link = ok(
        await uc.AddDocumentLink(repo)(ADMIN, title="OMS", description=None, url="https://who.int/docs/manual.pdf")
    )
    assert link.file_url and not link.has_stored_file and not link.is_previewable
    assert link.file_name == "manual.pdf" and link.file_type == "PDF"
    err(
        await uc.AddDocumentLink(repo)(ADMIN, title="x", description=None, url="javascript:alert(1)"), ErrorKind.INVALID
    )
    err(await uc.AddDocumentLink(repo)(DOCTOR, title="x", description=None, url="https://a.cu"), ErrorKind.FORBIDDEN)


async def test_anyone_can_view_previewable_inline(repo, storage):
    doc = ok(await upload(repo, storage))
    served = ok(await uc.GetDocumentFile(repo, storage)(doc.id, Disposition.INLINE))
    assert served.disposition is Disposition.INLINE
    assert served.media_type == "application/pdf"
    assert served.path.read_bytes() == PDF


async def test_non_previewable_is_forced_to_download(repo, storage):
    doc = ok(await upload(repo, storage, filename="checklist.docx", data=DOCX))
    served = ok(await uc.GetDocumentFile(repo, storage)(doc.id, Disposition.INLINE))
    assert served.disposition is Disposition.ATTACHMENT


async def test_file_errors(repo, storage):
    err(await uc.GetDocumentFile(repo, storage)(uuid4(), Disposition.ATTACHMENT), ErrorKind.NOT_FOUND)
    link = ok(await uc.AddDocumentLink(repo)(ADMIN, title="x", description=None, url="https://a.cu/b.pdf"))
    err(await uc.GetDocumentFile(repo, storage)(link.id, Disposition.ATTACHMENT), ErrorKind.NOT_FOUND)
    doc = ok(await upload(repo, storage))
    storage.files.clear()  # fichero perdido en disco
    err(await uc.GetDocumentFile(repo, storage)(doc.id, Disposition.ATTACHMENT), ErrorKind.NOT_FOUND)


async def test_delete_removes_row_and_file_only_for_managers(repo, storage):
    doc = ok(await upload(repo, storage))
    err(await uc.DeleteDocument(repo, storage)(DOCTOR, doc.id), ErrorKind.FORBIDDEN)
    ok(await uc.DeleteDocument(repo, storage)(ADMIN, doc.id))
    assert repo.rows == {} and storage.files == {}
    err(await uc.DeleteDocument(repo, storage)(ADMIN, doc.id), ErrorKind.NOT_FOUND)


async def test_list_and_search(repo, storage):
    ok(await upload(repo, storage))
    assert len(await uc.ListDocuments(repo)()) == 1
    assert len(await uc.ListDocuments(repo)("inform")) == 1
    assert await uc.ListDocuments(repo)("nada") == []


# ---------- adaptador de disco ----------


def test_local_storage_roundtrip_and_key_guard(tmp_path):
    storage = LocalFileStorage(tmp_path)
    key = "0123456789abcdef0123456789abcdef.pdf"
    storage.save(key, PDF)
    path = storage.path(key)
    assert path is not None and path.read_bytes() == PDF and path.parent.name == "01"
    storage.delete(key)
    assert storage.path(key) is None
    assert storage.path("../../etc/passwd") is None
    storage.delete("../../etc/passwd")  # no lanza ni toca nada fuera
    with pytest.raises(ValueError):
        storage.save("../fuera.pdf", PDF)
    assert not list(tmp_path.rglob(".upload-*"))  # sin temporales huérfanos
