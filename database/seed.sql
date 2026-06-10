-- Datos iniciales opcionales (sin usuarios; usar python -m app.scripts.seed para usuarios)

INSERT INTO contact_info (organization_name, address, phone, email, schedule) VALUES
(
    'Hospital Oncológico de La Habana',
    'Calzada de Finlay, La Habana, Cuba',
    '+53 7 649 0000',
    'contacto@holh.sld.cu',
    'Lunes a Viernes: 8:00 - 16:30'
) ON CONFLICT DO NOTHING;

INSERT INTO diseases (name, description) VALUES
('Cáncer de mama', 'Neoplasia maligna de mama'),
('Cáncer de pulmón', 'Neoplasia maligna de pulmón'),
('Cáncer colorrectal', 'Neoplasia maligna de colon y recto'),
('Leucemia', 'Neoplasias hematológicas malignas'),
('Melanoma', 'Melanoma maligno de piel')
ON CONFLICT (name) DO NOTHING;

INSERT INTO interest_links (title, url, description, sort_order) VALUES
('Sociedad Española de Oncología Médica', 'https://www.seom.org', 'Recursos y guías clínicas', 1),
('OMS - Cáncer', 'https://www.who.int/es/health-topics/cancer', 'Información global sobre cáncer', 2),
('Portal de Ensayos Clínicos', 'https://clinicaltrials.gov', 'Búsqueda de ensayos clínicos', 3);

INSERT INTO news (title, summary, content, is_published) VALUES
(
    'Bienvenidos al Portal del Hospital Oncológico de La Habana',
    'Plataforma institucional de recursos clínicos para profesionales de la salud.',
    'Este portal centraliza noticias, guías de diagnóstico, protocolos de tratamiento y documentación de referencia del Hospital Oncológico de La Habana.',
    TRUE
);
