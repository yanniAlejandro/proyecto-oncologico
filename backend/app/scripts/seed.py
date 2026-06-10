"""Script para crear usuario administrador inicial."""
import asyncio

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.models.contact import ContactInfo
from app.models.disease import Disease
from app.models.interest_link import InterestLink
from app.models.news import News
from app.models.user import User, UserRole


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

        encargado = await db.execute(select(User).where(User.email == "encargado@oncologico.com"))
        if encargado.scalar_one_or_none() is None:
            db.add(
                User(
                    email="encargado@oncologico.com",
                    password_hash=hash_password("Encargado123!"),
                    full_name="Encargado Clínico",
                    role=UserRole.ENCARGADO,
                )
            )

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

        news_count = await db.execute(select(News))
        if not news_count.scalars().first():
            db.add(
                News(
                    title="Bienvenidos al Portal del Hospital Oncológico de La Habana",
                    summary="Plataforma institucional de recursos clínicos para profesionales de la salud.",
                    content="Este portal centraliza noticias, guías de diagnóstico, protocolos de tratamiento y documentación de referencia del Hospital Oncológico de La Habana.",
                    is_published=True,
                )
            )

        await db.commit()
        print("Seed completado.")
        print("Admin: admin@oncologico.com / Admin123!")
        print("Encargado: encargado@oncologico.com / Encargado123!")
        print("Médico: medico@oncologico.com / Medico123!")


if __name__ == "__main__":
    asyncio.run(seed())
