"""Carga guías de diagnóstico, protocolos de tratamiento y documentos de ejemplo."""
import asyncio

from sqlalchemy import select

from app.core.database import async_session
from app.models.diagnostic_guide import DiagnosticGuide
from app.models.disease import Disease
from app.models.document import Document
from app.models.treatment_protocol import TreatmentProtocol
from app.models.user import User

GUIDES = [
    {
        "disease": "Cáncer de mama",
        "title": "Guía de diagnóstico — Cáncer de mama en estadio temprano",
        "content": """CRITERIOS DE SOSPECHA
- Nódulo mamario palpable o hallazgo imagenológico BI-RADS 4-5
- Secreción papilar hemática unilateral
- Cambios cutáneos: retracción, edema tipo piel de naranja

ESTUDIO INICIAL
1. Anamnesis y examen físico completo (mamas, axilas, supraclavicular)
2. Mamografía bilateral + ecografía mamaria
3. Biopsia con aguja gruesa (core biopsy) o PAAF según indicación

CONFIRMACIÓN HISTOLÓGICA
- Tipo histológico (carcinoma ductal/lobulillar)
- Grado de Nottingham
- Receptores hormonales (ER, PR)
- HER2 (IHC y/o FISH)
- Ki-67

ESTADIFICACIÓN
- TAC tórax-abdomen-pelvis o PET-CT según estadio clínico
- Gammagrafía ósea si síntomas o laboratorio alterado
- RM mamaria en casos seleccionados (mama densa, multifocalidad)

NOTAS INSTITUCIONALES
Seguir algoritmo del comité oncológico mamario del HOLH.""",
    },
    {
        "disease": "Cáncer de mama",
        "title": "Guía de diagnóstico — Metástasis óseas en cáncer de mama",
        "content": """INDICACIONES DE ESTUDIO
- Dolor óseo persistente no explicado
- Hipercalcemia o elevación de fosfatasas alcalinas
- Sospecha clínica en paciente con antecedente de cáncer de mama

MÉTODOS DIAGNÓSTICOS
1. Gammagrafía ósea de cuerpo completo
2. RM de columna si compromiso medular
3. Biopsia ósea si lesión única y duda diagnóstica

CONFIRMACIÓN
- Correlacionar con perfil inmunohistoquímico del tumor primario
- Documentar extensión: oligometastásico vs polimetastásico

SEGUIMIENTO
Repetir estudios según respuesta al tratamiento sistémico.""",
    },
    {
        "disease": "Cáncer de pulmón",
        "title": "Guía de diagnóstico — Cáncer de pulmón de células no pequeñas (CPNPC)",
        "content": """SOSPECHA CLÍNICA
- Tos persistente, hemoptisis, disnea progresiva
- Derrame pleural unilateral
- Síndrome constitucional y adenopatías

ESTUDIO INICIAL
1. Radiografía de tórax → TAC de tórax con contraste
2. Espirometría y evaluación funcional respiratoria
3. PET-CT para estadificación si candidato a tratamiento curativo

OBTENCIÓN DE MUESTRA
- Broncoscopia con biopsia transbronquial
- EBUS para mediastino
- Biopsia percutánea guiada por TAC si lesión periférica

ANATOMÍA PATOLÓGICA
- Subtipo histológico (adenocarcinoma, escamoso, etc.)
- PD-L1
- Estudios moleculares: EGFR, ALK, ROS1, BRAF, KRAS, MET según indicación

ESTADIFICACIÓN TNM (8ª edición)
Documentar T, N, M antes de iniciar tratamiento.""",
    },
    {
        "disease": "Cáncer de pulmón",
        "title": "Guía de diagnóstico — Cáncer de pulmón microcítico (CPMC)",
        "content": """CARACTERÍSTICAS
- Crecimiento rápido, alta agresividad
- Frecuente presentación con enfermedad extensa

ESTUDIO OBLIGATORIO
1. TAC tórax-abdomen con contraste
2. RM cerebral (alta incidencia de metástasis SNC)
3. Biopsia para confirmación histológica

MARCADORES Y LABORATORIO
- LDH, electrolitos (síndrome de secreción inadecuada de ADH)
- CEA, pro-GRP según disponibilidad

CLASIFICACIÓN
- Enfermedad limitada vs extensa
- Evaluación cardiopulmonar para quimiorradioterapia concurrente

URGENCIAS ONCOLÓGICAS
Descartar compresión medular y síndrome de vena cava superior.""",
    },
    {
        "disease": "Cáncer colorrectal",
        "title": "Guía de diagnóstico — Cáncer colorrectal localizado",
        "content": """SOSPECHA
- Alteración del ritmo intestinal, rectorragia, anemia ferropénica
- Pérdida de peso inexplicada en mayores de 50 años

ESTUDIO ENDOSCÓPICO
1. Colonoscopia completa hasta ciego
2. Biopsia de todas las lesiones sospechosas
3. Marcar lesión si abordaje quirúrgico planificado

IMÁGENES
- TAC tórax-abdomen-pelvis con contraste
- RM pélvica en cáncer de recto (estadiaje local)
- CEA basal

FACTORES MOLECULARES
- Estudio de MSI/MMR en todos los casos
- RAS/BRAF si enfermedad metastásica

PREPARACIÓN QUIRÚRGICA
Evaluación anestésica y nutricional según protocolo del servicio.""",
    },
    {
        "disease": "Leucemia",
        "title": "Guía de diagnóstico — Leucemia mieloide aguda (LMA)",
        "content": """PRESENTACIÓN
- Citopenias (anemia, neutropenia, trombocitopenia)
- Blastos en sangre periférica
- Infiltración extramedular (encías, piel)

ESTUDIOS DE LABORATORIO
1. Hemograma con fórmula leucocitaria
2. Frotis de sangre periférica y médula ósea
3. Coagulación (descartar coagulación intravascular diseminada)

INMUNOFENOTIPO Y GENÉTICA
- Citometría de flujo en médula ósea
- Cariotipo y estudios moleculares (FLT3, NPM1, CEBPA, etc.)

ESTADIFICACIÓN Y COMPLICACIONES
- Evaluar infiltración del SNC (punción lumbar si indicado)
- ECG y ecocardiograma antes de antraciclinas

MANEJO INICIAL
Clasificar riesgo y derivar a hematología oncológica de forma urgente.""",
    },
    {
        "disease": "Melanoma",
        "title": "Guía de diagnóstico — Melanoma cutáneo primario",
        "content": """SOSPECHA CLÍNICA
Regla ABCDE: Asimetría, Bordes irregulares, Color heterogéneo, Diámetro >6 mm, Evolución

EXAMEN DERMATOLÓGICO
- Inspección de cuerpo completo incluyendo mucosas y uñas
- Evaluación de linfonodos regionales

CONFIRMACIÓN
1. Biopsia excisional con márgenes estrechos (1-3 mm)
2. No realizar shave biopsy en lesiones sospechosas

ANATOMÍA PATOLÓGICA
- Espesor de Breslow (determinante pronóstico principal)
- Nivel de Clark
- Ulceración, mitosis/mm²
- Márgenes quirúrgicos

ESTADIFICACIÓN
- PET-CT o TAC si Breslow >4 mm o adenopatías
- LDH en estadio avanzado""",
    },
    {
        "disease": "Melanoma",
        "title": "Guía de diagnóstico — Melanoma metastásico",
        "content": """CRITERIOS DE ENFERMEDAD AVANZADA
- Metástasis a distancia (pulmón, hígado, SNC, hueso)
- Enfermedad ganglionar no resecable

ESTUDIOS DE EXTENSIÓN
1. TAC tórax-abdomen-pelvis con contraste
2. RM cerebral
3. PET-CT si disponible

BIOLOGÍA MOLECULAR
- Mutación BRAF V600
- NRAS, c-KIT según subtipo

MARCADORES
- LDH (factor pronóstico en estadio IV)
- Evaluación de síntomas neurológicos

ENFOQUE MULTIDISCIPLINARIO
Presentar en comité de melanoma para definir inmunoterapia, terapia dirigida o quimioterapia.""",
    },
]

PROTOCOLS = [
    {
        "disease": "Cáncer de mama",
        "title": "Protocolo de tratamiento — Cáncer de mama luminal A (estadio I-II)",
        "content": """INDICACIÓN
Pacientes con RH+/HER2-, bajo índice de proliferación (Ki-67 bajo)

CIRUGÍA
- Conservadora de mama + radioterapia, o mastectomía según preferencia y tamaño tumoral
- Biopsia de ganglio centinela

TRATAMIENTO ADYUVANTE SISTÉMICO
- Tamoxifeno 20 mg/día VO por 5-10 años (premenopáusicas)
- Inhibidor de aromatasa + supresión ovárica si indicado

RADIOTERAPIA
- Toda la mama tras cirugía conservadora
- Considerar boost al lecho tumoral

SEGUIMIENTO
Controles cada 3-6 meses los primeros 2 años, luego anual.""",
    },
    {
        "disease": "Cáncer de mama",
        "title": "Protocolo de tratamiento — Cáncer de mama HER2 positivo",
        "content": """INDICACIÓN
Tumores HER2+ (IHC 3+ o FISH amplificado)

NEOADYUVANCIA/ADYUVANCIA
- Antraciclinas + taxanos + trastuzumab
- Pertuzumab en enfermedad de alto riesgo

DURACIÓN ANTI-HER2
- Trastuzumab por 12 meses total
- Monitoreo cardíaco (ecocardiograma basal y periódico)

ENFERMEDAD METASTÁSICA
- Trastuzumab + taxano ± pertuzumab como primera línea
- T-DM1 tras progresión
- Tucatinib + trastuzumab + capecitabina si metástasis SNC""",
    },
    {
        "disease": "Cáncer de pulmón",
        "title": "Protocolo de tratamiento — CPNPC con mutación EGFR",
        "content": """INDICACIÓN
Adenocarcinoma de pulmón con mutación activadora de EGFR

PRIMERA LÍNEA
- Osimertinib 80 mg/día VO (preferido en todas las variantes EGFR)
- Alternativa: gefitinib o erlotinib si osimertinib no disponible

MONITOREO
- TAC cada 8-12 semanas
- Evaluar toxicidad cutánea y pulmonar

PROGRESIÓN
- Rebiopsia líquida o tisular para mecanismos de resistencia (T790M, C797S)
- Considerar quimioterapia platinada o ensayo clínico

SOPORTE
Manejo de diarrea, rash acneiforme y toxicidad intersticial pulmonar.""",
    },
    {
        "disease": "Cáncer de pulmón",
        "title": "Protocolo de tratamiento — CPNPC sin driver, PD-L1 ≥50%",
        "content": """INDICACIÓN
CPNPC avanzado sin mutaciones accionables, PD-L1 ≥50%

PRIMERA LÍNEA
- Pembrolizumab 200 mg IV cada 3 semanas (hasta 35 ciclos o 2 años)
- Alternativa: atezolizumab según disponibilidad

CRITERIOS DE RESPUESTA
- RECIST 1.1 cada 9-12 semanas
- Vigilar toxicidad inmunomediada (tiroiditis, colitis, neumonitis)

SI PROGRESIÓN
- Carboplatino + pemetrexed ± pembrolizumab
- Docetaxel en segunda línea

EDUCACIÓN AL PACIENTE
Informar sobre signos de alerta de toxicidad inmunológica.""",
    },
    {
        "disease": "Cáncer colorrectal",
        "title": "Protocolo de tratamiento — Cáncer de colon estadio III",
        "content": """INDICACIÓN
Post-resección de cáncer de colon con afectación ganglionar (estadio III)

CIRUGÍA
- Colectomía oncológica con linfadenectomía ≥12 ganglios

QUIMIOTERAPIA ADYUVANTE
- FOLFOX x 6 meses (oxaliplatino + 5-FU/leucovorin)
- Alternativa CAPOX si perfil de toxicidad lo permite

CONTRAINDICACIONES OXALIPLATINO
- Neuropatía periférica preexistente severa
- Reducir dosis según tolerancia

SEGUIMIENTO
- CEA cada 3 meses x 2 años
- TAC anual x 3 años
- Colonoscopia a los 12 meses""",
    },
    {
        "disease": "Cáncer colorrectal",
        "title": "Protocolo de tratamiento — CCR metastásico MSI-H/dMMR",
        "content": """INDICACIÓN
Enfermedad metastásica con alta inestabilidad de microsatélites

PRIMERA LÍNEA
- Pembrolizumab 200 mg IV cada 3 semanas
- Respuestas duraderas frecuentes

ALTERNATIVAS
- Nivolumab + ipilimumab en progresión o según comité

NO RECOMENDADO
- Quimioterapia convencional como primera opción si MSI-H confirmado

MONITOREO
Evaluar respuesta clínica e imagenológica cada 12 semanas.""",
    },
    {
        "disease": "Leucemia",
        "title": "Protocolo de tratamiento — LMA de riesgo intermedio (inducción)",
        "content": """INDICACIÓN
LMA de novo, apta para quimioterapia intensiva

INDUCCIÓN (7+3)
- Citarabina 100-200 mg/m²/día x 7 días
- Daunorrubicina 60-90 mg/m²/día x 3 días (o idarubicina)

EVALUACIÓN DÍA 14-21
- Mielograma de control
- Soporte transfusional y antimicrobiano

CONSOLIDACIÓN
- Ciclos adicionales según riesgo citogenético/molecular
- Considerar trasplante alogénico si factores de mal pronóstico

SOPORTE
- Profilaxis antifúngica y antiviral
- Aislamiento protector durante neutropenia""",
    },
    {
        "disease": "Leucemia",
        "title": "Protocolo de tratamiento — Leucemia linfoblástica aguda (LLA) en adultos",
        "content": """INDUCCIÓN
- Esquema tipo Hyper-CVAD alternado con metotrexato/citarabina de alta dosis
- Profilaxis del SNC desde el inicio (intratecal)

SUBTIPOS
- LLA BCR-ABL+: añadir inhibidor de tirosina quinasa (dasatinib/imatinib)
- LLA con fenotipo de células T: considerar nelarabina

CONSOLIDACIÓN Y MANTENIMIENTO
- 2-3 años de terapia total según protocolo
- Trasplante alogénico en alto riesgo o recaída

MONITOREO
- MRD (enfermedad residual mínima) por citometría de flujo""",
    },
    {
        "disease": "Melanoma",
        "title": "Protocolo de tratamiento — Melanoma estadio III resecado",
        "content": """INDICACIÓN
Melanoma estadio III tras linfadenectomía completa

OPCIÓN 1 — INMUNOTERAPIA ADYUVANTE
- Nivolumab 240 mg IV cada 2 semanas x 12 meses
- Alternativa: pembrolizumab 200 mg IV cada 3 semanas x 12 meses

OPCIÓN 2 — TERAPIA DIRIGIDA (BRAF V600+)
- Dabrafenib + trametinib por 12 meses

SEGUIMIENTO
- Examen físico y LDH cada 3 meses
- TAC y RM cerebral según riesgo

RECURRENCIA
Re-estadificar y presentar en comité para terapia sistémica.""",
    },
    {
        "disease": "Melanoma",
        "title": "Protocolo de tratamiento — Melanoma metastásico irresecable",
        "content": """PRIMERA LÍNEA — INMUNOTERAPIA
- Nivolumab + ipilimumab (BRAF no mutado o indiferente)
- Pembrolizumab monoterapia si comorbilidades

BRAF V600 MUTADO
- Dabrafenib + trametinib
- Encorafenib + binimetinib según disponibilidad

SEGUNDA LÍNEA
- Inmunoterapia si no usada previamente
- Quimioterapia (dacarbazina) si no candidato a IO

METÁSTASIS SNC
- Considerar radiocirugía + IO o terapia dirigida BRAF/MEK""",
    },
]

DOCUMENTS = [
    {
        "title": "Manual de procedimientos oncológicos HOLH",
        "description": "Procedimientos estandarizados de atención oncológica del hospital.",
        "file_name": "manual-procedimientos-holh.pdf",
        "file_url": "https://www.who.int/docs/default-source/cancer-documents/cancer-control-manual-es.pdf",
        "file_type": "PDF",
    },
    {
        "title": "Consentimiento informado — Quimioterapia",
        "description": "Modelo de consentimiento informado para tratamiento con quimioterapia sistémica.",
        "file_name": "consentimiento-quimioterapia.pdf",
        "file_url": "https://www.mscbs.gob.es/profesionales/proteccionSalud/prevencion/docs/consentimiento_informado.pdf",
        "file_type": "PDF",
    },
    {
        "title": "Consentimiento informado — Radioterapia",
        "description": "Modelo de consentimiento informado para tratamiento radioterápico.",
        "file_name": "consentimiento-radioterapia.pdf",
        "file_url": "https://www.mscbs.gob.es/profesionales/proteccionSalud/prevencion/docs/consentimiento_informado.pdf",
        "file_type": "PDF",
    },
    {
        "title": "Guía de manejo de toxicidades — Quimioterapia",
        "description": "Algoritmos para evaluación y manejo de efectos adversos de quimioterapia.",
        "file_name": "guia-toxicidades-quimioterapia.pdf",
        "file_url": "https://www.esmo.org/guidelines/supportive-and-palliative-care",
        "file_type": "PDF",
    },
    {
        "title": "Lista de verificación pre-quimioterapia",
        "description": "Checklist obligatorio antes de administrar primera dosis de quimioterapia.",
        "file_name": "checklist-pre-quimioterapia.docx",
        "file_url": "https://www.cancer.gov/about-cancer/treatment/chemotherapy",
        "file_type": "DOCX",
    },
    {
        "title": "Formulario de derivación al comité oncológico",
        "description": "Formato para presentación de casos en comité multidisciplinario.",
        "file_name": "formulario-comite-oncologico.docx",
        "file_url": "https://www.seom.org/seomcms/images/stories/recursos/FORMULARIO_COMITE.pdf",
        "file_type": "DOCX",
    },
    {
        "title": "Protocolo de bioseguridad en oncología",
        "description": "Normas de manipulación segura de citostáticos y residuos peligrosos.",
        "file_name": "protocolo-bioseguridad-oncologia.pdf",
        "file_url": "https://www.who.int/publications/i/item/9789241547671",
        "file_type": "PDF",
    },
    {
        "title": "Guía de nutrición en pacientes oncológicos",
        "description": "Recomendaciones nutricionales para pacientes en tratamiento activo.",
        "file_name": "guia-nutricion-oncologica.pdf",
        "file_url": "https://www.esmo.org/guidelines/supportive-and-palliative-care",
        "file_type": "PDF",
    },
    {
        "title": "Escala de evaluación del dolor oncológico",
        "description": "Instrumentos EVA y escala numérica para valoración del dolor.",
        "file_name": "escala-dolor-oncologico.pdf",
        "file_url": "https://www.who.int/teams/mental-health-and-substance-use/treatment-care/mental-health-gap-action-programme/evidence-based-guidelines",
        "file_type": "PDF",
    },
    {
        "title": "Normas de archivo y historia clínica oncológica",
        "description": "Criterios de documentación clínica y archivo de historias oncológicas.",
        "file_name": "normas-historia-clinica-oncologica.pdf",
        "file_url": "https://www.paho.org/es/documentos/normas-estandarizacion-registros-medicos",
        "file_type": "PDF",
    },
    {
        "title": "Guía de cuidados paliativos",
        "description": "Abordaje integral del paciente oncológico en situación paliativa.",
        "file_name": "guia-cuidados-paliativos.pdf",
        "file_url": "https://www.who.int/teams/mental-health-and-substance-use/treatment-care/mental-health-gap-action-programme/evidence-based-guidelines",
        "file_type": "PDF",
    },
    {
        "title": "Solicitud de estudios imagenológicos",
        "description": "Formulario estandarizado para solicitud de TAC, RM y PET-CT.",
        "file_name": "solicitud-estudios-imagen.docx",
        "file_url": "https://www.cancer.gov/about-cancer/diagnosis-staging/ct-scans-fact-sheet",
        "file_type": "DOCX",
    },
]


async def seed_clinical():
    async with async_session() as db:
        diseases_result = await db.execute(select(Disease))
        diseases = {d.name: d for d in diseases_result.scalars().all()}
        if not diseases:
            print("Error: no hay enfermedades. Ejecuta primero python -m app.scripts.seed")
            return

        encargado = (
            await db.execute(select(User).where(User.email == "encargado@oncologico.com"))
        ).scalar_one_or_none()

        guides_added = 0
        for item in GUIDES:
            exists = await db.execute(
                select(DiagnosticGuide).where(DiagnosticGuide.title == item["title"])
            )
            if exists.scalar_one_or_none():
                continue
            disease = diseases.get(item["disease"])
            if not disease:
                print(f"Enfermedad no encontrada: {item['disease']}")
                continue
            db.add(
                DiagnosticGuide(
                    disease_id=disease.id,
                    title=item["title"],
                    content=item["content"],
                    created_by=encargado.id if encargado else None,
                )
            )
            guides_added += 1

        protocols_added = 0
        for item in PROTOCOLS:
            exists = await db.execute(
                select(TreatmentProtocol).where(TreatmentProtocol.title == item["title"])
            )
            if exists.scalar_one_or_none():
                continue
            disease = diseases.get(item["disease"])
            if not disease:
                print(f"Enfermedad no encontrada: {item['disease']}")
                continue
            db.add(
                TreatmentProtocol(
                    disease_id=disease.id,
                    title=item["title"],
                    content=item["content"],
                    created_by=encargado.id if encargado else None,
                )
            )
            protocols_added += 1

        documents_added = 0
        for item in DOCUMENTS:
            exists = await db.execute(select(Document).where(Document.title == item["title"]))
            if exists.scalar_one_or_none():
                continue
            db.add(
                Document(
                    title=item["title"],
                    description=item["description"],
                    file_name=item["file_name"],
                    file_url=item["file_url"],
                    file_type=item["file_type"],
                    uploaded_by=encargado.id if encargado else None,
                )
            )
            documents_added += 1

        await db.commit()
        print(f"Guías de diagnóstico añadidas: {guides_added}")
        print(f"Protocolos de tratamiento añadidos: {protocols_added}")
        print(f"Documentos del repositorio añadidos: {documents_added}")


if __name__ == "__main__":
    asyncio.run(seed_clinical())
