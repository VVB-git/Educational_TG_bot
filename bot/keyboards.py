from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.roles import Role, ROLES, reader_roles

BTN_LIMIT = 64


def button_label(text: str, limit: int = BTN_LIMIT) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _builder() -> InlineKeyboardBuilder:
    return InlineKeyboardBuilder()


def roles_keyboard() -> InlineKeyboardMarkup:
    builder = _builder()
    for role in ROLES:
        builder.row(InlineKeyboardButton(text=button_label(role.title), callback_data=f"role:{role.id}"))
    return builder.as_markup()


def topics_keyboard(topics: list[dict], role_id: str) -> InlineKeyboardMarkup:
    builder = _builder()
    for topic in topics:
        builder.row(
            InlineKeyboardButton(text=button_label(topic["title"]), callback_data=f"tp:{topic['id']}")
        )
    builder.row(InlineKeyboardButton(text="Сменить роль", callback_data="br"))
    return builder.as_markup()


def questions_keyboard(questions: list[dict], role_id: str, topic_id: int) -> InlineKeyboardMarkup:
    builder = _builder()
    for question in questions:
        builder.row(
            InlineKeyboardButton(text=button_label(question["title"]), callback_data=f"qs:{question['id']}")
        )
    builder.row(InlineKeyboardButton(text="К темам", callback_data=f"bt:{role_id}"))
    builder.row(InlineKeyboardButton(text="Сменить роль", callback_data="br"))
    return builder.as_markup()


def answer_keyboard(role_id: str, topic_id: int) -> InlineKeyboardMarkup:
    builder = _builder()
    builder.row(InlineKeyboardButton(text="К списку вопросов", callback_data=f"bq:{topic_id}"))
    builder.row(InlineKeyboardButton(text="К темам", callback_data=f"bt:{role_id}"))
    builder.row(InlineKeyboardButton(text="Сменить роль", callback_data="br"))
    return builder.as_markup()


def admin_roles_keyboard() -> InlineKeyboardMarkup:
    builder = _builder()
    for role in reader_roles():
        builder.row(
            InlineKeyboardButton(text=button_label(role.title), callback_data=f"ar:{role.id}")
        )
    builder.row(InlineKeyboardButton(text="Сменить роль", callback_data="br"))
    return builder.as_markup()


def admin_topics_keyboard(topics: list[dict], role: Role) -> InlineKeyboardMarkup:
    builder = _builder()
    for topic in topics:
        builder.row(
            InlineKeyboardButton(text=button_label(topic["title"]), callback_data=f"at:{topic['id']}")
        )
    builder.row(InlineKeyboardButton(text="Новая тема", callback_data="an"))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="xx"))
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = _builder()
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="xx"))
    return builder.as_markup()


def answer_collect_keyboard() -> InlineKeyboardMarkup:
    builder = _builder()
    builder.row(InlineKeyboardButton(text="Готово", callback_data="dn"))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="xx"))
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = _builder()
    builder.row(InlineKeyboardButton(text="Сохранить", callback_data="ok"))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="xx"))
    return builder.as_markup()
