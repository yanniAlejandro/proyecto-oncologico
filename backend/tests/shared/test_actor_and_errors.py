import pytest
from fastapi import HTTPException

from app.shared.domain.actor import (
    ALL_SECTIONS,
    Actor,
    Role,
    Section,
    normalize_permissions,
    require_admin,
    require_section,
    require_user,
)
from app.shared.domain.result import AppError, Err, ErrorKind, Ok
from app.shared.presentation.errors import unwrap
from tests.fakes import ADMIN, DOCTOR, EDITOR
from tests.helpers import err, ok


def test_require_section_401_visitor_403_without_permission():
    err(require_section(None, Section.DOCUMENTOS), ErrorKind.UNAUTHENTICATED)
    err(require_section(DOCTOR, Section.DOCUMENTOS), ErrorKind.FORBIDDEN)
    assert ok(require_section(EDITOR, Section.DOCUMENTOS)) is EDITOR
    assert ok(require_section(ADMIN, Section.DOCUMENTOS)) is ADMIN


def test_doctor_permissions_are_per_section():
    doc = Actor(id=DOCTOR.id, role=Role.MEDICO, permissions=frozenset({Section.PUBLICACIONES}))
    assert doc.can(Section.PUBLICACIONES)
    assert not doc.can(Section.GUIAS)
    err(require_section(doc, Section.GUIAS), ErrorKind.FORBIDDEN)


def test_admin_has_every_section_implicitly():
    assert ADMIN.permissions == frozenset()
    assert ADMIN.effective_permissions == ALL_SECTIONS
    assert DOCTOR.effective_permissions == frozenset()


def test_require_user_and_admin():
    err(require_user(None), ErrorKind.UNAUTHENTICATED)
    assert ok(require_user(DOCTOR)) is DOCTOR
    err(require_admin(EDITOR), ErrorKind.FORBIDDEN)
    err(require_admin(None), ErrorKind.UNAUTHENTICATED)
    assert ok(require_admin(ADMIN)) is ADMIN


def test_normalize_permissions_drops_unknown_values():
    assert normalize_permissions(["guias", "obsoleta", Section.ENLACES]) == {Section.GUIAS, Section.ENLACES}


def test_encargado_role_no_longer_exists():
    assert {r.value for r in Role} == {"administrador", "medico"}


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (AppError.invalid("x"), 400),
        (AppError.unauthenticated(), 401),
        (AppError.forbidden(), 403),
        (AppError.not_found("x"), 404),
        (AppError.conflict("x"), 409),
        (AppError.too_large("x"), 413),
    ],
)
def test_unwrap_maps_errors_to_http(error, status):
    with pytest.raises(HTTPException) as exc:
        unwrap(Err(error))
    assert exc.value.status_code == status
    assert exc.value.detail == error.message


def test_unwrap_returns_value():
    assert unwrap(Ok(42)) == 42
