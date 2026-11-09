from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.features.auth.application.use_cases import Login
from app.features.auth.presentation.deps import CurrentActor, login_use_case
from app.features.users.presentation.deps import Users
from app.shared.domain.result import AppError
from app.shared.presentation.errors import raise_http, unwrap

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    permissions: list[str]
    """Secciones que puede gestionar (todas si es administrador)."""


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, uc: Annotated[Login, Depends(login_use_case)]):
    return TokenResponse(access_token=unwrap(await uc(payload.email, payload.password)))


@router.get("/me", response_model=MeResponse)
async def me(actor: CurrentActor, users: Users):
    if actor is None:
        raise_http(AppError.unauthenticated())
    user = await users.get(actor.id)
    assert user is not None  # ResolveActor ya comprobó que existe y está activo
    return MeResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        permissions=sorted(s.value for s in actor.effective_permissions),
    )
