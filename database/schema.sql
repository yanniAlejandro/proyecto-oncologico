-- Base de datos: Sistema Oncológico
-- PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE user_role AS ENUM ('administrador', 'encargado', 'medico');

-- Usuarios
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    role        user_role NOT NULL DEFAULT 'medico',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);

-- Enfermedades (catálogo compartido)
CREATE TABLE diseases (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_diseases_name ON diseases (name);

-- Noticias
CREATE TABLE news (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(500) NOT NULL,
    summary     TEXT,
    content     TEXT NOT NULL,
    author_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_created_at ON news (created_at DESC);
CREATE INDEX idx_news_published ON news (is_published);

-- Guías de diagnóstico
CREATE TABLE diagnostic_guides (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disease_id  UUID NOT NULL REFERENCES diseases(id) ON DELETE RESTRICT,
    title       VARCHAR(500) NOT NULL,
    content     TEXT NOT NULL,
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_diagnostic_guides_disease ON diagnostic_guides (disease_id);
CREATE INDEX idx_diagnostic_guides_title ON diagnostic_guides (title);

-- Protocolos de tratamiento
CREATE TABLE treatment_protocols (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disease_id  UUID NOT NULL REFERENCES diseases(id) ON DELETE RESTRICT,
    title       VARCHAR(500) NOT NULL,
    content     TEXT NOT NULL,
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_treatment_protocols_disease ON treatment_protocols (disease_id);
CREATE INDEX idx_treatment_protocols_title ON treatment_protocols (title);

-- Repositorio de documentos
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(500) NOT NULL,
    description TEXT,
    file_name   VARCHAR(500) NOT NULL,
    file_url    VARCHAR(1000) NOT NULL,
    file_type   VARCHAR(100),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_title ON documents (title);

-- Enlaces de interés
CREATE TABLE interest_links (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(500) NOT NULL,
    url         VARCHAR(1000) NOT NULL,
    description TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interest_links_order ON interest_links (sort_order);

-- Información de contacto (registro único)
CREATE TABLE contact_info (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_name VARCHAR(255) NOT NULL DEFAULT 'Hospital Oncológico de La Habana',
    address     TEXT,
    phone       VARCHAR(50),
    email       VARCHAR(255),
    schedule    TEXT,
    map_url     VARCHAR(1000),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_news_updated_at
    BEFORE UPDATE ON news FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_diagnostic_guides_updated_at
    BEFORE UPDATE ON diagnostic_guides FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_treatment_protocols_updated_at
    BEFORE UPDATE ON treatment_protocols FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_contact_info_updated_at
    BEFORE UPDATE ON contact_info FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
