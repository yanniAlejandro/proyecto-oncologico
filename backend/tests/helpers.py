"""Aserciones sobre Result."""

from app.shared.domain.result import Err, ErrorKind, Ok, Result


def ok[T](result: Result[T]) -> T:
    assert isinstance(result, Ok), f"se esperaba Ok y llegó {result!r}"
    return result.value


def err(result: Result[object], kind: ErrorKind) -> str:
    assert isinstance(result, Err), f"se esperaba Err({kind}) y llegó {result!r}"
    assert result.error.kind is kind, f"se esperaba {kind} y llegó {result.error.kind}: {result.error.message}"
    return result.error.message
