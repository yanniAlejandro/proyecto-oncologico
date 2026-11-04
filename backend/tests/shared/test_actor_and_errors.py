import pytest
from fastapi import HTTPException

from app.shared.domain.actor import ADMINS, CONTENT_MANAGERS, GUIDE_READERS, Role, can_manage_content, require
from app.shared.domain.result import AppError, Err, ErrorKind, Ok
from app.shared.presentation.errors import unwrap
from tests.fakes import ADMIN, DOCTOR, MANAGER
from tests.helpers import err, ok


def test_require_returns_401_for_visitor_and_403_for_wrong_role():
    err(require(None, ADMINS), ErrorKind.UNAUTHENTICATED)
    err(require(DOCTOR, CONTENT_MANAGERS), ErrorKind.FORBIDDEN)
    assert ok(require(MANAGER, CONTENT_MANAGERS)) is MANAGER


@pytest.mark.parametrize(
    ("role", "manage", "read_guides", "admin"),
    [
        (Role.ADMINISTRADOR, True, True, True),
        (Role.ENCARGADO, True, True, False),
        (Role.MEDICO, False, True, False),
    ],
)
def test_role_matrix(role, manage, read_guides, admin):
    assert (role in CONTENT_MANAGERS) is manage
    assert (role in GUIDE_READERS) is read_guides
    assert (role in ADMINS) is admin


def test_can_manage_content():
    assert can_manage_content(ADMIN) and can_manage_content(MANAGER)
    assert not can_manage_content(DOCTOR) and not can_manage_content(None)


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
