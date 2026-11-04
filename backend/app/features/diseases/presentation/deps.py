from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.diseases.domain.model import DiseaseRepository
from app.features.diseases.infrastructure.repository import SqlDiseaseRepository
from app.shared.infrastructure.database import get_session


def get_disease_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> DiseaseRepository:
    return SqlDiseaseRepository(session)


Diseases = Annotated[DiseaseRepository, Depends(get_disease_repository)]
