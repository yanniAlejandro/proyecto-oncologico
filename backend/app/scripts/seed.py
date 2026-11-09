"""Script para crear usuario administrador inicial."""

import asyncio

from sqlalchemy import select

from app.features.about.domain.model import slugify
from app.features.about.infrastructure.orm import AboutSectionRow as AboutSection
from app.features.contact.infrastructure.orm import ContactInfoRow as ContactInfo
from app.features.diseases.infrastructure.orm import DiseaseRow as Disease
from app.features.interest_links.infrastructure.orm import InterestLinkRow as InterestLink
from app.features.users.infrastructure.orm import UserPermissionRow as UserPermission
from app.features.users.infrastructure.orm import UserRow as User
from app.scripts.about_drafts import DRAFTS
from app.shared.domain.actor import Role as UserRole
from app.shared.domain.actor import Section
from app.shared.infrastructure import orm_registry  # noqa: F401
from app.shared.infrastructure.database import async_session
from app.shared.infrastructure.security import BcryptPasswordHasher

hash_password = BcryptPasswordHasher().hash


async def seed():
    async with async_session() as db:
        admin = await db.execute(select(User).where(User.email == "admin@oncologico.com"))
        if admin.scalar_one_or_none() is None:
            db.add(
                User(
                    email="admin@oncologico.com",
                    password_hash=hash_password("Admin123!"),
                    full_name="Administrador del Sistema",
                    role=UserRole.ADMINISTRADOR,
                )
            )

        editora = await db.execute(select(User).where(User.email == "editora@oncologico.com"))
        if editora.scalar_one_or_none() is None:
            row = User(
                email="editora@oncologico.com",
                password_hash=hash_password("Editora123!"),
                full_name="Dra. María González",
                role=UserRole.MEDICO,
            )
            # Médico con permisos de gestión concedidos (ejemplo del modelo de permisos).
            row.permission_rows = [
                UserPermission(section=s.value) for s in (Section.PUBLICACIONES, Section.DOCUMENTOS, Section.ENLACES)
            ]
            db.add(row)

        medico = await db.execute(select(User).where(User.email == "medico@oncologico.com"))
        if medico.scalar_one_or_none() is None:
            db.add(
                User(
                    email="medico@oncologico.com",
                    password_hash=hash_password("Medico123!"),
                    full_name="Dr. Juan Pérez",
                    role=UserRole.MEDICO,
                )
            )

        contact = await db.execute(select(ContactInfo).limit(1))
        if contact.scalar_one_or_none() is None:
            db.add(
                ContactInfo(
                    organization_name="Hospital Oncológico de La Habana",
                    address="Calzada de Finlay, La Habana, Cuba",
                    phone="+53 7 649 0000",
                    email="contacto@holh.sld.cu",
                    schedule="Lunes a Viernes: 8:00 - 16:30",
                )
            )

        diseases_count = await db.execute(select(Disease))
        if not diseases_count.scalars().first():
            db.add_all(
                [
                    Disease(name="Cáncer de mama", description="Neoplasia maligna de mama"),
                    Disease(name="Cáncer de pulmón", description="Neoplasia maligna de pulmón"),
                    Disease(name="Cáncer colorrectal", description="Neoplasia maligna de colon y recto"),
                    Disease(name="Leucemia", description="Neoplasias hematológicas malignas"),
                    Disease(name="Melanoma", description="Melanoma maligno de piel"),
                ]
            )

        links_count = await db.execute(select(InterestLink))
        if not links_count.scalars().first():
            db.add_all(
                [
                    InterestLink(
                        title="Sociedad Española de Oncología Médica",
                        url="https://www.seom.org",
                        description="Recursos y guías clínicas",
                        sort_order=1,
                    ),
                    InterestLink(
                        title="OMS - Cáncer",
                        url="https://www.who.int/es/health-topics/cancer",
                        description="Información global sobre cáncer",
                        sort_order=2,
                    ),
                ]
            )

        about = await db.execute(select(AboutSection).limit(1))
        if about.scalar_one_or_none() is None:
            for order, (title, body) in enumerate(DRAFTS, start=1):
                db.add(AboutSection(slug=slugify(title), title=title, body=body, sort_order=order * 10))

        await db.commit()
        print("Seed completado.")
        print("Admin: admin@oncologico.com / Admin123!")
        print("Médico con permisos: editora@oncologico.com / Editora123!")
        print("Médico: medico@oncologico.com / Medico123!")


if __name__ == "__main__":
    asyncio.run(seed())
