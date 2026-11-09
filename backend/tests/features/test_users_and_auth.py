from uuid import uuid4

from app.features.auth.application.use_cases import Login, ResolveActor
from app.features.users.application.use_cases import CreateUser, DeactivateUser, ListUsers, UpdateUser
from app.shared.domain.actor import Actor, Role, Section
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, EDITOR, FakeHasher, FakeTokens, FakeUsers
from tests.helpers import err, ok


def make():
    users = FakeUsers.with_actors(ADMIN, EDITOR, DOCTOR)
    return users, FakeHasher(), FakeTokens()


async def test_only_admin_lists_users():
    users, _, _ = make()
    assert len(ok(await ListUsers(users)(ADMIN))) == 3
    err(await ListUsers(users)(EDITOR), ErrorKind.FORBIDDEN)
    err(await ListUsers(users)(None), ErrorKind.UNAUTHENTICATED)


async def test_new_doctor_has_no_permissions_by_default():
    users, hasher, _ = make()
    user = ok(
        await CreateUser(users, hasher)(ADMIN, email=" Nuevo@Holh.SLD.cu ", password="secreto1", full_name=" Dra. Ana ")
    )
    assert user.email == "nuevo@holh.sld.cu"
    assert user.full_name == "Dra. Ana"
    assert user.role is Role.MEDICO
    assert user.permissions == frozenset()
    assert user.password_hash == "hashed:secreto1"


async def test_admin_creates_doctor_with_permissions_and_other_admins():
    users, hasher, _ = make()
    create = CreateUser(users, hasher)
    doc = ok(
        await create(
            ADMIN, email="d@b.cu", password="secreto1", full_name="Dr. D", permissions=frozenset({Section.GUIAS})
        )
    )
    assert doc.permissions == {Section.GUIAS}
    admin = ok(
        await create(
            ADMIN,
            email="a@b.cu",
            password="secreto1",
            full_name="Admin 2",
            role=Role.ADMINISTRADOR,
            permissions=frozenset({Section.GUIAS}),
        )
    )
    assert admin.role is Role.ADMINISTRADOR and admin.permissions == frozenset()  # implícitas, no se guardan


async def test_create_rejects_duplicates_short_passwords_and_non_admins():
    users, hasher, _ = make()
    create = CreateUser(users, hasher)
    err(await create(ADMIN, email="a@b.cu", password="123", full_name="Xx"), ErrorKind.INVALID)
    err(await create(ADMIN, email="MEDICO@test.cu", password="secreto1", full_name="Xx"), ErrorKind.CONFLICT)
    err(await create(EDITOR, email="a@b.cu", password="secreto1", full_name="Xx"), ErrorKind.FORBIDDEN)


async def test_admin_grants_and_revokes_permissions():
    users, hasher, _ = make()
    update = UpdateUser(users, hasher)
    granted = ok(await update(ADMIN, DOCTOR.id, permissions=frozenset({Section.PUBLICACIONES, Section.DOCUMENTOS})))
    assert granted.permissions == {Section.PUBLICACIONES, Section.DOCUMENTOS}
    revoked = ok(await update(ADMIN, DOCTOR.id, permissions=frozenset()))
    assert revoked.permissions == frozenset()
    err(await update(EDITOR, DOCTOR.id, permissions=frozenset({Section.GUIAS})), ErrorKind.FORBIDDEN)


async def test_promote_to_admin_clears_loose_permissions_and_password_reset():
    users, hasher, _ = make()
    update = UpdateUser(users, hasher)
    promoted = ok(await update(ADMIN, EDITOR.id, role=Role.ADMINISTRADOR))
    assert promoted.role is Role.ADMINISTRADOR and promoted.permissions == frozenset()
    reset = ok(await update(ADMIN, DOCTOR.id, password="nuevaclave"))
    assert reset.password_hash == "hashed:nuevaclave"
    err(await update(ADMIN, DOCTOR.id, password="123"), ErrorKind.INVALID)


async def test_admin_safeguards():
    users, hasher, _ = make()
    update = UpdateUser(users, hasher)
    err(await update(ADMIN, ADMIN.id, is_active=False), ErrorKind.INVALID)
    err(await update(ADMIN, ADMIN.id, role=Role.MEDICO), ErrorKind.INVALID)
    err(await update(ADMIN, uuid4(), full_name="Nadie"), ErrorKind.NOT_FOUND)

    # Con dos admins, uno puede degradar al otro; pero nunca quedarse en cero.
    second = ok(
        await CreateUser(users, hasher)(
            ADMIN, email="b@b.cu", password="secreto1", full_name="Admin B", role=Role.ADMINISTRADOR
        )
    )
    second_actor = Actor(id=second.id, role=Role.ADMINISTRADOR)
    ok(await update(second_actor, ADMIN.id, role=Role.MEDICO))
    err(await update(second_actor, second.id, is_active=False), ErrorKind.INVALID)
    assert await users.count_active_admins() == 1


async def test_last_admin_cannot_be_deactivated_by_anyone():
    users, hasher, _ = make()
    users.rows[EDITOR.id].role = Role.ADMINISTRADOR
    users.rows[EDITOR.id].is_active = False  # admin inactivo: no cuenta
    other = Actor(id=EDITOR.id, role=Role.ADMINISTRADOR)
    err(await UpdateUser(users, hasher)(other, ADMIN.id, is_active=False), ErrorKind.INVALID)


async def test_deactivate_is_update_shortcut():
    users, hasher, _ = make()
    deactivate = DeactivateUser(users, hasher)
    ok(await deactivate(ADMIN, DOCTOR.id))
    assert users.rows[DOCTOR.id].is_active is False
    err(await deactivate(ADMIN, ADMIN.id), ErrorKind.INVALID)
    ok(await UpdateUser(users, hasher)(ADMIN, DOCTOR.id, is_active=True))
    assert users.rows[DOCTOR.id].is_active is True


async def test_login_issues_token_and_hides_which_part_failed():
    users, hasher, tokens = make()
    login = Login(users, hasher, tokens)
    assert ok(await login("medico@TEST.cu", "medico")) == f"token:{DOCTOR.id}"
    wrong_pw = err(await login("medico@test.cu", "nope"), ErrorKind.UNAUTHENTICATED)
    unknown = err(await login("nadie@test.cu", "x"), ErrorKind.UNAUTHENTICATED)
    assert wrong_pw == unknown == "Credenciales inválidas"


async def test_inactive_user_cannot_login_nor_be_resolved():
    users, hasher, tokens = make()
    users.rows[DOCTOR.id].is_active = False
    err(await Login(users, hasher, tokens)("medico@test.cu", "medico"), ErrorKind.UNAUTHENTICATED)
    assert await ResolveActor(users, tokens)(f"token:{DOCTOR.id}") is None


async def test_resolve_actor_carries_current_permissions():
    users, hasher, tokens = make()
    resolve = ResolveActor(users, tokens)
    actor = await resolve(f"token:{DOCTOR.id}")
    assert actor is not None and actor.role is Role.MEDICO and actor.permissions == frozenset()
    await UpdateUser(users, hasher)(ADMIN, DOCTOR.id, permissions=frozenset({Section.ENLACES}))
    actor = await resolve(f"token:{DOCTOR.id}")
    assert actor is not None and actor.can(Section.ENLACES)  # efecto inmediato, sin re-login
    assert await resolve(None) is None
    assert await resolve("basura") is None
