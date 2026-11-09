from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.features.auth.application.use_cases import Login, ResolveActor
from app.features.auth.domain.ports import TokenService
from app.features.users.presentation.deps import Hasher, Users
from app.shared.domain.actor import Actor
from app.shared.infrastructure.security import JwtTokenService

bearer = HTTPBearer(auto_error=False)


def get_token_service() -> TokenService:
    return JwtTokenService()


Tokens = Annotated[TokenService, Depends(get_token_service)]


def login_use_case(users: Users, hasher: Hasher, tokens: Tokens) -> Login:
    return Login(users, hasher, tokens)


async def get_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    users: Users,
    tokens: Tokens,
) -> Actor | None:
    """Actor del request; ``None`` si es visitante. Los casos de uso deciden 401/403."""
    token = credentials.credentials if credentials else None
    return await ResolveActor(users, tokens)(token)


CurrentActor = Annotated[Actor | None, Depends(get_actor)]
