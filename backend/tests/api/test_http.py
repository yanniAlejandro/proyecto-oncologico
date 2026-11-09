import pytest

from tests.api.conftest import MAX_UPLOAD, World

PDF = b"%PDF-1.4 prueba"


def test_health(world: World):
    assert world.client.get("/health").json() == {"status": "ok"}


def test_login_and_me(world: World):
    c = world.client
    r = c.post("/api/v1/auth/login", json={"email": "medico@test.cu", "password": "medico"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"
    me = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["role"] == "medico"
    assert c.post("/api/v1/auth/login", json={"email": "medico@test.cu", "password": "x"}).status_code == 401
    assert c.get("/api/v1/auth/me").status_code == 401
    assert c.get("/api/v1/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401


# Matriz de permisos: (método, ruta, cuerpo) → estado esperado por rol.
ROLES = [None, "medico", "editor", "admin"]
MATRIX = [
    ("GET", "/api/v1/publications", None, [200, 200, 200, 200]),
    ("GET", "/api/v1/about", None, [200, 200, 200, 200]),
    ("GET", "/api/v1/helpline", None, [200, 200, 200, 200]),
    ("GET", "/api/v1/helpline/professionals", None, [401, 403, 200, 200]),
    ("PUT", "/api/v1/helpline", {"phone": "+53 7 649 0000"}, [401, 403, 200, 200]),
    ("POST", "/api/v1/publications/preview", {"url": "https://desconocida.cu"}, [401, 403, 200, 200]),
    ("GET", "/api/v1/diagnostic-guides", None, [401, 200, 200, 200]),
    ("GET", "/api/v1/treatment-protocols", None, [401, 200, 200, 200]),
    ("GET", "/api/v1/documents", None, [200, 200, 200, 200]),
    ("GET", "/api/v1/users", None, [401, 403, 403, 200]),
    ("POST", "/api/v1/diseases", {"name": "Linfoma"}, [401, 403, 201, 409]),
    ("PUT", "/api/v1/contact", {"phone": "1"}, [401, 403, 403, 200]),
    ("DELETE", "/api/v1/documents/00000000-0000-0000-0000-000000000000", None, [401, 403, 404, 404]),
    ("POST", "/api/v1/interest-links", {"title": "x", "url": "https://x.cu"}, [401, 403, 201, 201]),
]


@pytest.mark.parametrize(("method", "path", "body", "expected"), MATRIX)
def test_role_matrix(world: World, method, path, body, expected):
    got = [world.client.request(method, path, json=body, headers=world.as_(role)).status_code for role in ROLES]
    assert got == expected


def test_guide_crud_and_validation(world: World):
    c, h = world.client, world.as_("editor")
    disease_id = str(world.diseases.by_name("Leucemia").id)
    assert (
        c.post(
            "/api/v1/diagnostic-guides",
            json={"disease_id": "no-uuid", "title": "abc", "content": "0123456789"},
            headers=h,
        ).status_code
        == 422
    )
    r = c.post(
        "/api/v1/diagnostic-guides",
        json={"disease_id": disease_id, "title": "Guía LMA", "content": "criterios diagnósticos"},
        headers=h,
    )
    assert r.status_code == 201 and r.json()["disease_name"] == "Leucemia"
    gid = r.json()["id"]
    assert c.get(f"/api/v1/diagnostic-guides/{gid}").status_code == 401
    assert c.get(f"/api/v1/diagnostic-guides/{gid}", headers=world.as_("medico")).status_code == 200
    assert c.put(f"/api/v1/diagnostic-guides/{gid}", json={"title": "Nuevo"}, headers=h).json()["title"] == "Nuevo"
    assert c.delete(f"/api/v1/diagnostic-guides/{gid}", headers=world.as_("medico")).status_code == 403
    assert c.delete(f"/api/v1/diagnostic-guides/{gid}", headers=h).status_code == 204
    assert c.get(f"/api/v1/diagnostic-guides/{gid}", headers=h).json()["detail"] == "Guía no encontrada"


def test_document_upload_view_download_delete(world: World):
    c, h = world.client, world.as_("editor")
    files = {"file": ("../Informe é.pdf", PDF, "application/pdf")}
    assert c.post("/api/v1/documents", data={"title": "Informe"}, files=files).status_code == 401
    assert (
        c.post("/api/v1/documents", data={"title": "Informe"}, files=files, headers=world.as_("medico")).status_code
        == 403
    )

    r = c.post("/api/v1/documents", data={"title": "Informe", "description": "anual"}, files=files, headers=h)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["file_name"] == "Informe é.pdf" and doc["has_file"] and doc["is_previewable"]

    # Visitante: ver en el navegador y descargar.
    view = c.get(f"/api/v1/documents/{doc['id']}/file", params={"disposition": "inline"})
    assert view.status_code == 200 and view.content == PDF
    assert view.headers["content-type"] == "application/pdf"
    assert view.headers["content-disposition"].startswith("inline;")
    assert view.headers["x-content-type-options"] == "nosniff"
    head = c.head(f"/api/v1/documents/{doc['id']}/file", params={"disposition": "inline"})
    assert head.status_code == 200 and head.content == b""  # el visor comprueba antes de incrustar
    down = c.get(f"/api/v1/documents/{doc['id']}/file")
    assert down.headers["content-disposition"].startswith("attachment;")
    assert "Informe%20%C3%A9.pdf" in down.headers["content-disposition"]

    assert c.delete(f"/api/v1/documents/{doc['id']}", headers=world.as_("medico")).status_code == 403
    assert c.delete(f"/api/v1/documents/{doc['id']}", headers=h).status_code == 204
    assert c.get(f"/api/v1/documents/{doc['id']}/file").status_code == 404
    assert c.head(f"/api/v1/documents/{doc['id']}/file").status_code == 404
    assert world.storage.files == {}


def test_document_upload_rejections(world: World):
    c, h = world.client, world.as_("admin")
    assert c.post("/api/v1/documents", data={"title": "Sin nada"}, headers=h).status_code == 400
    assert (
        c.post(
            "/api/v1/documents", data={"title": "ab"}, headers=h, files={"file": ("a.pdf", PDF, "application/pdf")}
        ).status_code
        == 422
    )
    fake = c.post(
        "/api/v1/documents", data={"title": "Falso"}, headers=h, files={"file": ("a.pdf", b"<html>", "application/pdf")}
    )
    assert fake.status_code == 400 and "PDF" in fake.json()["detail"]
    big = c.post(
        "/api/v1/documents",
        data={"title": "Grande"},
        headers=h,
        files={"file": ("a.pdf", PDF + b"x" * MAX_UPLOAD, "application/pdf")},
    )
    assert big.status_code == 413
    assert world.storage.files == {}


def test_document_external_link_and_policy(world: World):
    c, h = world.client, world.as_("editor")
    r = c.post("/api/v1/documents", data={"title": "Manual OMS", "file_url": "https://who.int/m.pdf"}, headers=h)
    assert r.status_code == 201 and r.json()["has_file"] is False and r.json()["file_url"]
    assert c.get(f"/api/v1/documents/{r.json()['id']}/file").status_code == 404
    policy = c.get("/api/v1/documents/upload-policy").json()
    assert ".pdf" in policy["allowed_extensions"] and policy["max_bytes"] == MAX_UPLOAD


def test_admin_creates_and_deactivates_doctor(world: World):
    c, h = world.client, world.as_("admin")
    r = c.post(
        "/api/v1/users", json={"email": "nueva@holh.cu", "password": "secreto1", "full_name": "Dra. Nueva"}, headers=h
    )
    assert r.status_code == 201 and r.json()["role"] == "medico"
    dup = c.post("/api/v1/users", json={"email": "NUEVA@holh.cu", "password": "secreto1", "full_name": "Xx"}, headers=h)
    assert dup.status_code == 409
    unknown_role = c.post(
        "/api/v1/users",
        json={"email": "e@holh.cu", "password": "secreto1", "full_name": "Xx", "role": "encargado"},
        headers=h,
    )
    assert unknown_role.status_code == 422
    assert c.delete(f"/api/v1/users/{r.json()['id']}", headers=h).status_code == 204
    assert c.post("/api/v1/auth/login", json={"email": "nueva@holh.cu", "password": "secreto1"}).status_code == 401


def test_permission_granted_over_http_takes_effect_immediately(world: World):
    c, admin, doctor = world.client, world.as_("admin"), world.as_("medico")
    link = {"title": "OMS", "url": "https://who.int"}
    assert c.post("/api/v1/interest-links", json=link, headers=doctor).status_code == 403
    me = c.get("/api/v1/auth/me", headers=doctor).json()
    assert me["permissions"] == []

    r = c.patch(f"/api/v1/users/{me['id']}", json={"permissions": ["enlaces"]}, headers=admin)
    assert r.status_code == 200 and r.json()["permissions"] == ["enlaces"]
    assert c.get("/api/v1/auth/me", headers=doctor).json()["permissions"] == ["enlaces"]
    assert c.post("/api/v1/interest-links", json=link, headers=doctor).status_code == 201
    assert c.post("/api/v1/diseases", json={"name": "Linfoma"}, headers=doctor).status_code == 403

    bad = c.patch(f"/api/v1/users/{me['id']}", json={"permissions": ["inventada"]}, headers=admin)
    assert bad.status_code == 422
    assert c.patch(f"/api/v1/users/{me['id']}", json={"permissions": []}, headers=doctor).status_code == 403


def test_admin_me_lists_every_section(world: World):
    perms = world.client.get("/api/v1/auth/me", headers=world.as_("admin")).json()["permissions"]
    assert "publicaciones" in perms and "linea_ayuda" in perms


def test_admin_cannot_lock_themselves_out(world: World):
    c, h = world.client, world.as_("admin")
    me = c.get("/api/v1/auth/me", headers=h).json()
    assert c.delete(f"/api/v1/users/{me['id']}", headers=h).status_code == 400
    assert c.patch(f"/api/v1/users/{me['id']}", json={"role": "medico"}, headers=h).status_code == 400


def test_publication_flow_with_preview_and_stored_image(world: World):
    from app.features.publications.domain.model import LinkPreview
    from tests.fakes import PNG

    url, image = "https://who.int/nota", "https://who.int/portada.png"
    world.previewer.pages[url] = LinkPreview(url=url, title="Nota OMS", description="Resumen", image_url=image)
    world.previewer.images[image] = PNG
    c, h = world.client, world.as_("editor")

    preview = c.post("/api/v1/publications/preview", json={"url": url}, headers=h).json()
    assert preview == {
        "found": True,
        "title": "Nota OMS",
        "description": "Resumen",
        "image_url": image,
        "site_name": None,
    }
    r = c.post(
        "/api/v1/publications",
        data={"title": preview["title"], "url": url, "description": preview["description"], "image_url": image},
        headers=h,
    )
    assert r.status_code == 201
    pub = r.json()
    assert pub["domain"] == "who.int" and pub["image_url"].startswith(f"/api/v1/publications/{pub['id']}/image")
    img = c.get(pub["image_url"])
    assert img.status_code == 200 and img.content == PNG and img.headers["content-type"] == "image/png"

    manual = c.put(
        f"/api/v1/publications/{pub['id']}",
        data={"title": "Nota OMS (editada)"},
        files={"image": ("foto.png", PNG, "image/png")},
        headers=h,
    )
    assert manual.status_code == 200 and manual.json()["title"] == "Nota OMS (editada)"
    bad = c.put(f"/api/v1/publications/{pub['id']}", files={"image": ("x.png", b"<svg/>", "image/png")}, headers=h)
    assert bad.status_code == 400
    assert c.delete(f"/api/v1/publications/{pub['id']}", headers=world.as_("medico")).status_code == 403
    assert c.delete(f"/api/v1/publications/{pub['id']}", headers=h).status_code == 204
    assert world.storage.files == {}


def test_about_section_crud_over_http(world: World):
    from tests.fakes import PNG

    c, h = world.client, world.as_("editor")
    r = c.post(
        "/api/v1/about",
        data={"title": "Oncología pediátrica", "body": "- Acompañamiento 24 h"},
        files={"image": ("sala.png", PNG, "image/png")},
        headers=h,
    )
    assert r.status_code == 201
    section = r.json()
    assert section["slug"] == "oncologia-pediatrica" and section["image_url"]
    assert c.get(section["image_url"]).content == PNG
    assert [s["title"] for s in c.get("/api/v1/about").json()] == ["Oncología pediátrica"]
    upd = c.put(f"/api/v1/about/{section['id']}", data={"remove_image": "true", "body": "Nuevo texto"}, headers=h)
    assert upd.status_code == 200 and upd.json()["image_url"] is None and upd.json()["body"] == "Nuevo texto"
    assert c.delete(f"/api/v1/about/{section['id']}", headers=world.as_("medico")).status_code == 403
    assert c.delete(f"/api/v1/about/{section['id']}", headers=h).status_code == 204


def test_helpline_public_view_with_availability(world: World):
    c, h = world.client, world.as_("editor")
    pro = {
        "full_name": "Dra. Ana Pérez",
        "specialty": "Oncología pediátrica",
        "phone": "+53 5 123 4567",
        "slots": [{"weekday": 0, "start": "09:00", "end": "11:00"}, {"weekday": 2, "start": "09:00", "end": "11:00"}],
    }
    assert c.post("/api/v1/helpline/professionals", json=pro, headers=h).status_code == 201
    bad = {**pro, "slots": [{"weekday": 0, "start": "12:00", "end": "09:00"}]}
    assert c.post("/api/v1/helpline/professionals", json=bad, headers=h).status_code == 422

    data = c.get("/api/v1/helpline").json()
    assert data["status"]["available_now"] is True  # lunes 10:00 La Habana, horario por defecto 8-16
    assert data["config"]["meets_minimum"] is True and len(data["config"]["daily_hours"]) == 7
    assert data["professionals"][0]["status"]["available_now"] is True
    assert data["weekdays"][0] == "Lunes"

    short = c.put("/api/v1/helpline", json={"slots": [{"weekday": 0, "start": "08:00", "end": "10:00"}]}, headers=h)
    assert short.status_code == 200 and short.json()["meets_minimum"] is False
