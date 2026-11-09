from typing import Protocol
from uuid import UUID


class TokenService(Protocol):
    def issue(self, user_id: UUID, role: str) -> str: ...
    def subject(self, token: str) -> UUID | None: ...
