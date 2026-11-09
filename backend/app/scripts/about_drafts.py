"""Borradores de «Quiénes somos» (pendientes de validar por el hospital).

Formato del texto: párrafos separados por línea en blanco, «- » para listas, «### » para
subtítulos, «**negrita**» y «> » para una nota destacada. Lo que va entre [corchetes] hay que completarlo.
Inspirados en los estándares de atención centrada en el paciente y la familia en oncología
pediátrica (SIOP Europe, «European Standards of Care for Children with Cancer») y en la Carta
Europea de los Derechos del Niño Hospitalizado (EACH).
"""

PENDING = (
    "> Borrador pendiente de validar por la dirección del centro. Los datos entre [corchetes] hay que completarlos."
)

DRAFTS: list[tuple[str, str]] = [
    (
        "El Centro de Oncología y Radiobiología",
        f"""{PENDING}

El Centro de Oncología y Radiobiología del Hospital Oncológico de La Habana pertenece al Sistema Nacional de Salud de Cuba. Se dedica a la prevención, el diagnóstico, el tratamiento y el seguimiento de las personas con cáncer, desde la infancia hasta la edad adulta.

Trabajamos con un modelo de **atención centrada en el paciente y su familia**: la familia forma parte del equipo de cuidado, recibe información clara y continua, y participa en las decisiones sobre el tratamiento.

### Misión
Ofrecer una atención oncológica integral, segura y humana, basada en la mejor evidencia científica, que acompañe al paciente y a su familia durante todo el proceso de la enfermedad.

### Nuestros valores
- **Humanidad**: trato digno, cercano y respetuoso con cada persona.
- **Trabajo en equipo**: decisiones tomadas por equipos multidisciplinarios.
- **Seguridad**: protocolos de tratamiento actualizados y prevención de riesgos.
- **Docencia e investigación**: formación continua de profesionales.

### Datos del centro
- Dirección: Calzada de Finlay, La Habana, Cuba
- Teléfono de atención: consulta la sección «Línea de ayuda»
- Correo electrónico: [completar]
- Dirección del centro: [completar]""",
    ),
    (
        "Salas y servicios",
        f"""{PENDING}

El centro reúne en un mismo lugar los servicios necesarios para el diagnóstico y el tratamiento del cáncer:

- **Consulta externa**: primera valoración, seguimiento y revisiones tras el tratamiento.
- **Hospitalización de adultos** y **sala de oncología pediátrica**.
- **Hospital de día**: tratamientos de quimioterapia que no requieren ingreso.
- **Radioterapia** y **radiobiología**.
- **Cirugía oncológica**.
- **Imagenología, laboratorio clínico y anatomía patológica**.
- **Cuidados paliativos y tratamiento del dolor**.
- **Psicología, trabajo social y nutrición**.
- **Farmacia oncológica**.

Los casos se presentan en **comités de tumores**, donde especialistas de distintas áreas acuerdan el mejor plan de tratamiento para cada paciente.

[Ajustar la lista a los servicios y salas reales del centro.]""",
    ),
    (
        "Oncología pediátrica",
        f"""{PENDING}

La sala de oncología pediátrica atiende a niños, niñas y adolescentes con cáncer, desde el nacimiento hasta los 18 años. Su organización sigue los estándares europeos de atención al niño con cáncer:

- **Equipo especializado** en oncología y hematología pediátrica, con enfermería formada en el cuidado del niño con cáncer.
- **Diagnóstico y tratamiento según protocolos** nacionales e internacionales, revisados en el comité de tumores pediátricos.
- **Acompañamiento permanente**: la madre, el padre o la persona cuidadora puede estar con el niño las 24 horas.
- **Apoyo psicológico y social** para el paciente, sus hermanos y su familia desde el diagnóstico.
- **Continuidad escolar** en el aula hospitalaria y **espacios de juego** adaptados a cada edad.
- **Control del dolor** y cuidados paliativos pediátricos cuando se necesitan.
- **Seguimiento a largo plazo** tras terminar el tratamiento y **transición** ordenada a las consultas de adultos.

[Completar: número de camas, edades atendidas y particularidades de la sala.]""",
    ),
    (
        "Derechos del paciente y su familia",
        f"""{PENDING}

Toda persona atendida en el centro, y en el caso de los menores también su familia, tiene derecho a:

- Recibir una **atención digna**, respetuosa con su intimidad, su cultura y sus creencias.
- Recibir **información comprensible**, adaptada a la edad del paciente, sobre el diagnóstico, el tratamiento, sus riesgos y las alternativas.
- **Participar en las decisiones** y dar o negar su **consentimiento informado**. Los niños y adolescentes deben ser escuchados y dar su asentimiento según su madurez.
- Estar **acompañado** por sus padres o por la persona cuidadora durante toda la estancia en el hospital.
- La **confidencialidad** de sus datos clínicos.
- Recibir **alivio del dolor** y cuidados paliativos cuando sea necesario.
- Mantener su **educación y su juego** durante la hospitalización.
- Presentar **quejas y sugerencias** y recibir respuesta.

### Compromisos de la familia
- Informar al equipo de cualquier cambio en el estado del paciente.
- Cumplir las normas de higiene y prevención de infecciones de la sala.
- Respetar la intimidad de los demás pacientes y familias.""",
    ),
    (
        "La sala, su entorno y el equipo asistencial",
        f"""{PENDING}

### El entorno
- Habitaciones preparadas para que un **acompañante** pueda permanecer junto al paciente.
- **Sala de juegos** y **aula hospitalaria**.
- Medidas de **prevención de infecciones**: lavado de manos al entrar y salir, y visitas sin síntomas de catarro o fiebre.
- Alimentación supervisada por el servicio de nutrición.

### El equipo asistencial
Cada paciente tiene un **médico de referencia** y una **enfermera de referencia**, que coordinan su atención y son el contacto principal de la familia. Con ellos trabajan:

- Oncólogos y hematólogos (de adultos y pediátricos), cirujanos y radioterapeutas.
- Enfermería especializada en oncología.
- Psicología, trabajo social, nutrición y fisioterapia.
- Maestros del aula hospitalaria.
- Equipo de cuidados paliativos y del dolor.

[Completar con los nombres de los responsables de la sala, si el hospital lo autoriza.]""",
    ),
    (
        "Horarios de visita y de información médica",
        f"""{PENDING}

### Acompañamiento
- En la sala de pediatría, la **madre, el padre o la persona cuidadora** puede acompañar al paciente **las 24 horas**.
- En las salas de adultos se permite un acompañante según indicación médica.

### Visitas
- Horario: [completar, por ejemplo de 15:00 a 18:00].
- Como máximo **dos visitantes** a la vez por paciente.
- No se permiten visitas de personas con fiebre, tos o catarro. Los niños pequeños solo pueden visitar con autorización del equipo.

### Información médica
- El **médico de referencia** informa a la familia **de lunes a viernes de [completar] a [completar]**, en un espacio privado.
- Los fines de semana y festivos, el médico de guardia informa si hay cambios importantes.
- Para dudas fuera de este horario, consulta la sección **«Línea de ayuda»**.""",
    ),
]
