from datetime import datetime

from pydantic import BaseModel, Field


class DiseaseOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class DiseaseCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None


class NewsCreate(BaseModel):
    title: str = Field(min_length=3)
    summary: str | None = None
    content: str = Field(min_length=10)
    is_published: bool = True


class NewsUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    content: str | None = None
    is_published: bool | None = None


class NewsOut(BaseModel):
    id: str
    title: str
    summary: str | None
    content: str
    author_name: str | None = None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class GuideCreate(BaseModel):
    disease_id: str
    title: str = Field(min_length=3)
    content: str = Field(min_length=10)


class GuideUpdate(BaseModel):
    disease_id: str | None = None
    title: str | None = None
    content: str | None = None


class GuideOut(BaseModel):
    id: str
    disease_id: str
    disease_name: str
    title: str
    content: str
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ProtocolCreate(BaseModel):
    disease_id: str
    title: str = Field(min_length=3)
    content: str = Field(min_length=10)


class ProtocolUpdate(BaseModel):
    disease_id: str | None = None
    title: str | None = None
    content: str | None = None


class ProtocolOut(BaseModel):
    id: str
    disease_id: str
    disease_name: str
    title: str
    content: str
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    title: str = Field(min_length=3)
    description: str | None = None
    file_name: str
    file_url: str
    file_type: str | None = None


class DocumentOut(BaseModel):
    id: str
    title: str
    description: str | None
    file_name: str
    file_url: str
    file_type: str | None
    uploader_name: str | None = None
    created_at: datetime


class InterestLinkCreate(BaseModel):
    title: str
    url: str
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class InterestLinkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class InterestLinkOut(BaseModel):
    id: str
    title: str
    url: str
    description: str | None
    sort_order: int
    is_active: bool


class ContactOut(BaseModel):
    id: str
    organization_name: str
    address: str | None
    phone: str | None
    email: str | None
    schedule: str | None
    map_url: str | None


class ContactUpdate(BaseModel):
    organization_name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    schedule: str | None = None
    map_url: str | None = None
