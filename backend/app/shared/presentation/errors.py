"""Traducción de ``Result``/``AppError`` a respuestas HTTP."""

from typing import NoReturn, TypeVar

from fastapi import HTTPException, status

from app.shared.domain.result import AppError, Err, ErrorKind, Ok, Result

T = TypeVar("T")

STATUS_BY_KIND = {
    ErrorKind.INVALID: status.HTTP_400_BAD_REQUEST,
    ErrorKind.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorKind.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    ErrorKind.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorKind.CONFLICT: status.HTTP_409_CONFLICT,
    ErrorKind.TOO_LARGE: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
}


def raise_http(error: AppError) -> NoReturn:
    raise HTTPException(status_code=STATUS_BY_KIND[error.kind], detail=error.message)


def unwrap(result: Result[T]) -> T:
    match result:
        case Ok(value):
            return value
        case Err(error):
            raise_http(error)
