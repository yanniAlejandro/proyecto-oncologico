from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.features.auth.presentation.deps import CurrentActor
from app.features.users.application.use_cases import CreateUser, DeactivateUser, ListUsers, UpdateUser
from app.features.users.presentation import deps
from app.features.users.presentation.schemas import UserCreate, UserOut, UserUpdate
from app.shared.presentation.errors import unwrap

router = APIRouter()


@router.get("", response_model=list[UserOut])
async def list_users(actor: CurrentActor, uc: Annotated[ListUsers, Depends(deps.list_users)]):
    return [UserOut.of(u) for u in unwrap(await uc(actor))]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, actor: CurrentActor, uc: Annotated[CreateUser, Depends(deps.create_user)]):
    user = unwrap(
        await uc(
            actor,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            permissions=frozenset(payload.permissions),
        )
    )
    return UserOut.of(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID, payload: UserUpdate, actor: CurrentActor, uc: Annotated[UpdateUser, Depends(deps.update_user)]
):
    user = unwrap(
        await uc(
            actor,
            user_id,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
            permissions=frozenset(payload.permissions) if payload.permissions is not None else None,
            password=payload.password,
        )
    )
    return UserOut.of(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID, actor: CurrentActor, uc: Annotated[DeactivateUser, Depends(deps.deactivate_user)]
):
    unwrap(await uc(actor, user_id))
