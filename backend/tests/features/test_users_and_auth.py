from app.features.auth.application.use_cases import Login, ResolveActor
from app.features.users.application.use_cases import CreateDoctor, DeactivateUser, ListUsers
from app.shared.domain.actor import Role
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, MANAGER, FakeHasher, FakeTokens, FakeUsers
from tests.helpers import err, ok


def make():
    users = FakeUsers.with_actors(ADMIN, MANAGER, DOCTOR)
    return users, FakeHasher(), FakeTokens()


async def test_only_admin_lists_users():
    users, _, _ = make()
    assert len(ok(await ListUsers(users)(ADMIN))) == 3
    err(await ListUsers(users)(MANAGER), ErrorKind.FORBIDDEN)
    err(await ListUsers(users)(None), ErrorKind.UNAUTHENTICATED)


async def test_admin_creates_doctor_with_normalized_email_and_hashed_password():
    users, hasher, _ = make()
    user = ok(
        await CreateDoctor(users, hasher)(
            ADMIN, email=" Nuevo@Holh.SLD.cu ", password="secreto1", full_name=" Dra. Ana "
        )
    )
    assert user.email == "nuevo@holh.sld.cu"
    assert user.full_name == "Dra. Ana"
    assert user.role is Role.MEDICO
    assert user.password_hash == "hashed:secreto1"


async def test_cannot_create_other_roles_duplicates_or_short_passwords():
    users, hasher, _ = make()
    create = CreateDoctor(users, hasher)
    err(await create(ADMIN, email="a@b.cu", password="secreto1", full_name="X", role=Role.ENCARGADO), ErrorKind.INVALID)
    err(await create(ADMIN, email="a@b.cu", password="123", full_name="X"), ErrorKind.INVALID)
    err(await create(ADMIN, email="MEDICO@test.cu", password="secreto1", full_name="X"), ErrorKind.CONFLICT)
    err(await create(MANAGER, email="a@b.cu", password="secreto1", full_name="X"), ErrorKind.FORBIDDEN)


async def test_deactivate_only_doctors_and_never_self():
    users, _, _ = make()
    deactivate = DeactivateUser(users)
    ok(await deactivate(ADMIN, DOCTOR.id))
    assert users.rows[DOCTOR.id].is_active is False
    err(await deactivate(ADMIN, ADMIN.id), ErrorKind.INVALID)
    err(await deactivate(ADMIN, MANAGER.id), ErrorKind.INVALID)
    err(await deactivate(ADMIN, MANAGER.id.__class__(int=0)), ErrorKind.NOT_FOUND)


async def test_login_issues_token_and_hides_which_part_failed():
    users, hasher, tokens = make()
    login = Login(users, hasher, tokens)
    assert ok(await login("medico@TEST.cu", "medico")) == f"token:{DOCTOR.id}"
    wrong_pw = err(await login("medico@test.cu", "nope"), ErrorKind.UNAUTHENTICATED)
    unknown = err(await login("nadie@test.cu", "x"), ErrorKind.UNAUTHENTICATED)
    assert wrong_pw == unknown == "Credenciales inválidas"


async def test_inactive_user_cannot_login_nor_be_resolved():
    users, hasher, tokens = make()
    await users.set_active(DOCTOR.id, False)
    err(await Login(users, hasher, tokens)("medico@test.cu", "medico"), ErrorKind.UNAUTHENTICATED)
    assert await ResolveActor(users, tokens)(f"token:{DOCTOR.id}") is None


async def test_resolve_actor():
    users, _, tokens = make()
    resolve = ResolveActor(users, tokens)
    actor = await resolve(f"token:{MANAGER.id}")
    assert actor is not None and actor.role is Role.ENCARGADO
    assert await resolve(None) is None
    assert await resolve("basura") is None
