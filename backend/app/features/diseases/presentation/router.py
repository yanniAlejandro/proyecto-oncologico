from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.features.auth.presentation.deps import CurrentActor
from app.features.diseases.application.use_cases import CreateDisease, DeleteDisease, ListDiseases, UpdateDisease
from app.features.diseases.domain.model import Disease
from app.features.diseases.presentation.deps import Diseases
from app.shared.presentation.errors import unwrap

router = APIRouter()


class DiseaseCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None


class DiseaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=2)
    description: str | None = None


class DiseaseOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    @classmethod
    def of(cls, d: Disease) -> "DiseaseOut":
        return cls(id=str(d.id), name=d.name, description=d.description)


@router.get("", response_model=list[DiseaseOut])
async def list_diseases(diseases: Diseases, search: str | None = Query(None)):
    return [DiseaseOut.of(d) for d in await ListDiseases(diseases)(search)]


@router.post("", response_model=DiseaseOut, status_code=status.HTTP_201_CREATED)
async def create_disease(payload: DiseaseCreate, actor: CurrentActor, diseases: Diseases):
    return DiseaseOut.of(unwrap(await CreateDisease(diseases)(actor, payload.name, payload.description)))


@router.put("/{disease_id}", response_model=DiseaseOut)
async def update_disease(disease_id: UUID, payload: DiseaseUpdate, actor: CurrentActor, diseases: Diseases):
    result = await UpdateDisease(diseases)(actor, disease_id, name=payload.name, description=payload.description)
    return DiseaseOut.of(unwrap(result))


@router.delete("/{disease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disease(disease_id: UUID, actor: CurrentActor, diseases: Diseases):
    unwrap(await DeleteDisease(diseases)(actor, disease_id))
