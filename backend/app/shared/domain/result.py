"""Result explícito para fallos esperados de los casos de uso.

Los casos de uso devuelven ``Ok(valor)`` o ``Err(AppError)``; las excepciones
quedan para bugs. La capa HTTP traduce ``AppError.kind`` a código de estado.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

T = TypeVar("T")


class ErrorKind(StrEnum):
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    TOO_LARGE = "too_large"


@dataclass(frozen=True, slots=True)
class AppError:
    kind: ErrorKind
    message: str

    @classmethod
    def invalid(cls, message: str) -> AppError:
        return cls(ErrorKind.INVALID, message)

    @classmethod
    def not_found(cls, message: str) -> AppError:
        return cls(ErrorKind.NOT_FOUND, message)

    @classmethod
    def unauthenticated(cls, message: str = "No autenticado") -> AppError:
        return cls(ErrorKind.UNAUTHENTICATED, message)

    @classmethod
    def forbidden(cls, message: str = "Permisos insuficientes") -> AppError:
        return cls(ErrorKind.FORBIDDEN, message)

    @classmethod
    def conflict(cls, message: str) -> AppError:
        return cls(ErrorKind.CONFLICT, message)

    @classmethod
    def too_large(cls, message: str) -> AppError:
        return cls(ErrorKind.TOO_LARGE, message)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Err:
    error: AppError


type Result[T] = Ok[T] | Err
