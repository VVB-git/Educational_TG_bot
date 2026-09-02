from bot.config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    """Пока доступ к админке открыт всем (тест).

    Когда понадобится ограничение, раскомментируйте проверку ADMIN_IDS
    и пропишите id в .env. Хендлеры менять не нужно.
    """
    _ = user_id, ADMIN_IDS
    return True
    # return user_id in ADMIN_IDS
