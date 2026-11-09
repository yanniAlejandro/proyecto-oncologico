"""Fakes en memoria de los puertos (sin librería de mocks), al estilo tymp-native."""

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.features.clinical_content.domain.model import ClinicalDoc, ClinicalDraft
from app.features.contact.domain.model import DEFAULT_ORGANIZATION, ContactInfo
from app.features.diseases.domain.model import Disease
from app.features.documents.domain.model import Document, NewDocument
from app.features.interest_links.domain.model import InterestLink
from app.features.publications.domain.model import LinkPreview, NewPublication, Publication
from app.features.users.domain.model import NewUser, User, UserChanges
from app.shared.domain.actor import ALL_SECTIONS, Actor, Role


def now() -> datetime:
    return datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


def actor(role: Role | None, full_name: str = "") -> Actor | None:
    return None if role is None else Actor(id=uuid4(), role=role, full_name=full_name or role.value)


ADMIN = Actor(id=uuid4(), role=Role.ADMINISTRADOR, full_name="Admin")
# Médico al que un admin ha concedido todas las secciones (lo que antes hacía el encargado).
EDITOR = Actor(id=uuid4(), role=Role.MEDICO, full_name="Editora", permissions=ALL_SECTIONS)
DOCTOR = Actor(id=uuid4(), role=Role.MEDICO, full_name="Médico")
VISITOR: Actor | None = None


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


class FakeTokens:
    def issue(self, user_id: UUID, role: str) -> str:
        return f"token:{user_id}"

    def subject(self, token: str) -> UUID | None:
        try:
            return UUID(token.removeprefix("token:")) if token.startswith("token:") else None
        except ValueError:
            return None


def _key(a: Actor) -> str:
    return "editor" if a.permissions else a.role.value


class FakeUsers:
    def __init__(self, users: list[User] | None = None) -> None:
        self.rows: dict[UUID, User] = {u.id: u for u in users or []}

    @classmethod
    def with_actors(cls, *actors: Actor) -> "FakeUsers":
        return cls(
            [
                User(
                    id=a.id,
                    email=f"{_key(a)}@test.cu",
                    full_name=a.full_name,
                    role=a.role,
                    password_hash=f"hashed:{_key(a)}",
                    permissions=a.permissions,
                )
                for a in actors
            ]
        )

    async def get(self, user_id: UUID) -> User | None:
        return self.rows.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email.lower() == email.lower()), None)

    async def list_all(self) -> list[User]:
        return sorted(self.rows.values(), key=lambda u: u.full_name)

    async def add(self, new: NewUser) -> User:
        user = User(
            id=uuid4(),
            email=new.email,
            full_name=new.full_name,
            role=new.role,
            password_hash=new.password_hash,
            created_at=now(),
            permissions=new.permissions,
        )
        self.rows[user.id] = user
        return user

    async def update(self, user_id: UUID, changes: UserChanges) -> User | None:
        user = self.rows.get(user_id)
        if user is None:
            return None
        values = {k: getattr(changes, k) for k in UserChanges.__dataclass_fields__ if getattr(changes, k) is not None}
        self.rows[user_id] = replace(user, **values)
        return self.rows[user_id]

    async def count_active_admins(self) -> int:
        return sum(1 for u in self.rows.values() if u.role is Role.ADMINISTRADOR and u.is_active)


class FakeDiseases:
    def __init__(self, *names: str) -> None:
        self.rows: dict[UUID, Disease] = {}
        for name in names:
            d = Disease(id=uuid4(), name=name)
            self.rows[d.id] = d

    def by_name(self, name: str) -> Disease:
        return next(d for d in self.rows.values() if d.name == name)

    async def list(self, search: str | None = None) -> list[Disease]:
        items = sorted(self.rows.values(), key=lambda d: d.name)
        return [d for d in items if not search or search.lower() in d.name.lower()]

    async def get(self, disease_id: UUID) -> Disease | None:
        return self.rows.get(disease_id)

    async def get_by_name(self, name: str) -> Disease | None:
        return next((d for d in self.rows.values() if d.name.lower() == name.lower()), None)

    async def add(self, name: str, description: str | None) -> Disease:
        d = Disease(id=uuid4(), name=name, description=description)
        self.rows[d.id] = d
        return d


class FakePublications:
    def __init__(self) -> None:
        self.rows: dict[UUID, Publication] = {}
        self._tick = 0

    def _now(self) -> datetime:
        self._tick += 1
        return now().replace(second=self._tick % 60)

    async def list(self, search: str | None) -> list[Publication]:
        items = sorted(self.rows.values(), key=lambda p: p.created_at, reverse=True)
        if search:
            items = [p for p in items if search.lower() in f"{p.title} {p.description or ''} {p.url}".lower()]
        return items

    async def get(self, publication_id: UUID) -> Publication | None:
        return self.rows.get(publication_id)

    async def add(self, new: NewPublication) -> Publication:
        ts = self._now()
        p = Publication(
            id=uuid4(),
            title=new.title,
            url=new.url,
            description=new.description,
            image_key=new.image_key,
            created_at=ts,
            updated_at=ts,
            author_name=str(new.author_id),
        )
        self.rows[p.id] = p
        return p

    async def update(self, publication_id: UUID, changes: dict[str, object]) -> Publication | None:
        if publication_id not in self.rows:
            return None
        self.rows[publication_id] = replace(self.rows[publication_id], **changes, updated_at=self._now())
        return self.rows[publication_id]

    async def delete(self, publication_id: UUID) -> bool:
        return self.rows.pop(publication_id, None) is not None


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class FakePreviewer:
    """Internet simulado: URL → vista previa, URL de imagen → bytes."""

    def __init__(self, pages: dict[str, LinkPreview] | None = None, images: dict[str, bytes] | None = None) -> None:
        self.pages = pages or {}
        self.images = images or {}
        self.fetched: list[str] = []

    async def preview(self, url: str) -> LinkPreview | None:
        return self.pages.get(url)

    async def fetch_image(self, url: str) -> bytes | None:
        self.fetched.append(url)
        return self.images.get(url)


class FakeClinical:
    def __init__(self, diseases: FakeDiseases) -> None:
        self.rows: dict[UUID, ClinicalDoc] = {}
        self._diseases = diseases

    async def list(self, search: str | None) -> list[ClinicalDoc]:
        items = sorted(self.rows.values(), key=lambda d: d.title)
        if search:
            items = [d for d in items if search.lower() in f"{d.title} {d.disease_name} {d.content}".lower()]
        return items

    async def get(self, doc_id: UUID) -> ClinicalDoc | None:
        return self.rows.get(doc_id)

    async def add(self, draft: ClinicalDraft, author_id: UUID) -> ClinicalDoc:
        disease = self._diseases.rows[draft.disease_id]
        doc = ClinicalDoc(
            id=uuid4(),
            disease_id=disease.id,
            disease_name=disease.name,
            title=draft.title,
            content=draft.content,
            created_at=now(),
            updated_at=now(),
            author_name="autor",
        )
        self.rows[doc.id] = doc
        return doc

    async def update(self, doc_id: UUID, changes: dict[str, object]) -> ClinicalDoc | None:
        if doc_id not in self.rows:
            return None
        doc = replace(self.rows[doc_id], **changes)
        if "disease_id" in changes:
            doc = replace(doc, disease_name=self._diseases.rows[doc.disease_id].name)
        self.rows[doc_id] = doc
        return doc

    async def delete(self, doc_id: UUID) -> bool:
        return self.rows.pop(doc_id, None) is not None


class FakeDocuments:
    def __init__(self) -> None:
        self.rows: dict[UUID, Document] = {}
        self.fail_on_add = False

    async def list(self, search: str | None) -> list[Document]:
        items = sorted(self.rows.values(), key=lambda d: d.created_at, reverse=True)
        return [d for d in items if not search or search.lower() in f"{d.title} {d.description or ''}".lower()]

    async def get(self, doc_id: UUID) -> Document | None:
        return self.rows.get(doc_id)

    async def add(self, new: NewDocument) -> Document:
        if self.fail_on_add:
            raise RuntimeError("BD caída")
        doc = Document(
            id=uuid4(),
            title=new.title,
            description=new.description,
            file_name=new.file_name,
            created_at=now(),
            file_type=new.file_type,
            file_url=new.file_url,
            storage_key=new.storage_key,
            size_bytes=new.size_bytes,
            uploader_name="Encargado",
        )
        self.rows[doc.id] = doc
        return doc

    async def delete(self, doc_id: UUID) -> bool:
        return self.rows.pop(doc_id, None) is not None


class FakeStorage:
    """Almacenamiento en memoria; ``path`` materializa en un directorio temporal."""

    def __init__(self, tmp_dir: Path) -> None:
        self.files: dict[str, bytes] = {}
        self._tmp = tmp_dir

    def save(self, key: str, data: bytes) -> None:
        self.files[key] = data

    def path(self, key: str) -> Path | None:
        if key not in self.files:
            return None
        p = self._tmp / key
        p.write_bytes(self.files[key])
        return p

    def delete(self, key: str) -> None:
        self.files.pop(key, None)


class FakeLinks:
    def __init__(self) -> None:
        self.rows: dict[UUID, InterestLink] = {}

    async def list_active(self) -> list[InterestLink]:
        return sorted((link for link in self.rows.values() if link.is_active), key=lambda link: link.sort_order)

    async def add(self, data: dict[str, object]) -> InterestLink:
        defaults: dict[str, object] = {"description": None, "sort_order": 0, "is_active": True}
        link = InterestLink(id=uuid4(), **{**defaults, **data})  # type: ignore[arg-type]
        self.rows[link.id] = link
        return link

    async def update(self, link_id: UUID, changes: dict[str, object]) -> InterestLink | None:
        if link_id not in self.rows:
            return None
        self.rows[link_id] = replace(self.rows[link_id], **changes)
        return self.rows[link_id]

    async def delete(self, link_id: UUID) -> bool:
        return self.rows.pop(link_id, None) is not None


class FakeContact:
    def __init__(self, info: ContactInfo | None = None) -> None:
        self.info = info

    async def get(self) -> ContactInfo | None:
        return self.info

    async def upsert(self, changes: dict[str, object]) -> ContactInfo:
        base = self.info or ContactInfo(id=uuid4(), organization_name=DEFAULT_ORGANIZATION)
        self.info = replace(base, **changes)
        return self.info
