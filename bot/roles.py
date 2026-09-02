from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    id: str
    title: str
    kind: str  # "reader" | "admin"


# Новую роль добавляйте сюда — кнопка на /start появится сама.
ROLES: list[Role] = [
    Role(id="am_assistant", title="Ассистент аккаунт-менеджера", kind="reader"),
    Role(id="admin", title="Администратор", kind="admin"),
]


def get_role(role_id: str) -> Role | None:
    for role in ROLES:
        if role.id == role_id:
            return role
    return None


def reader_roles() -> list[Role]:
    return [role for role in ROLES if role.kind == "reader"]
