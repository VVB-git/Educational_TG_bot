from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.db import Database
from bot.keyboards import (
    admin_roles_keyboard,
    admin_topics_keyboard,
    answer_collect_keyboard,
    cancel_keyboard,
    confirm_keyboard,
    roles_keyboard,
)
from bot.roles import get_role
from bot.text_format import escape_html, user_text_to_html
from bot.ui import show_menu

router = Router()

PREVIEW_LIMIT = 800


class AdminFSM(StatesGroup):
    choosing_topic = State()
    waiting_topic_title = State()
    waiting_question = State()
    waiting_answer = State()
    confirming = State()


def _preview(html_text: str) -> str:
    import re

    plain = re.sub(r"<[^>]+>", "", html_text)
    plain = " ".join(plain.split())
    if len(plain) <= PREVIEW_LIMIT:
        return plain
    return plain[: PREVIEW_LIMIT - 1] + "…"


async def open_admin(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminFSM.choosing_topic)
    await show_menu(
        callback,
        "Режим администратора. Сейчас проверка доступа выключена — для теста.\n\n"
        "Выберите роль, для которой добавите вопрос.",
        admin_roles_keyboard(),
    )


@router.callback_query(F.data.startswith("ar:"))
async def admin_pick_role(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    role_id = callback.data.split(":", 1)[1]
    role = get_role(role_id)
    if role is None or role.kind != "reader":
        await callback.answer("Эту роль нельзя выбрать", show_alert=True)
        return

    topics = await db.list_topics(role_id)
    await state.set_state(AdminFSM.choosing_topic)
    await state.update_data(target_role_id=role_id, topic_id=None, topic_title=None, answer_parts=[])
    await show_menu(
        callback,
        f"Роль: {escape_html(role.title)}\n\nВыберите тему или создайте новую.",
        admin_topics_keyboard(topics, role),
    )


@router.callback_query(F.data == "an", AdminFSM.choosing_topic)
async def admin_new_topic(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.waiting_topic_title)
    await show_menu(callback, "Напишите название новой темы одним сообщением.", cancel_keyboard())


@router.callback_query(F.data.startswith("at:"), AdminFSM.choosing_topic)
async def admin_existing_topic(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    topic_id = int(callback.data.split(":", 1)[1])
    topic = await db.get_topic(topic_id)
    if topic is None:
        await callback.answer("Тема не найдена", show_alert=True)
        return
    await state.update_data(topic_id=topic_id, topic_title=topic["title"])
    await state.set_state(AdminFSM.waiting_question)
    await show_menu(
        callback,
        f"Тема: {escape_html(topic['title'])}\n\nНапишите текст кнопки-вопроса — как его увидит ассистент.",
        cancel_keyboard(),
    )


@router.message(AdminFSM.waiting_topic_title, F.text)
async def admin_topic_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer("Название пустое. Напишите ещё раз.", reply_markup=cancel_keyboard())
        return
    await state.update_data(topic_id=None, topic_title=title)
    await state.set_state(AdminFSM.waiting_question)
    await message.answer(
        f"Тема: {escape_html(title)}\n\nНапишите текст кнопки-вопроса — как его увидит ассистент.",
        reply_markup=cancel_keyboard(),
    )


@router.message(AdminFSM.waiting_topic_title)
async def admin_topic_title_not_text(message: Message) -> None:
    await message.answer("Нужен текст — название темы одним сообщением.", reply_markup=cancel_keyboard())


@router.message(AdminFSM.waiting_question, F.text)
async def admin_question_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer("Текст вопроса пустой. Напишите ещё раз.", reply_markup=cancel_keyboard())
        return
    await state.update_data(question_title=title, answer_parts=[])
    await state.set_state(AdminFSM.waiting_answer)
    await message.answer(
        "Теперь пришлите ответ. Можно несколькими сообщениями.\n"
        "Когда закончите — нажмите «Готово».",
        reply_markup=answer_collect_keyboard(),
    )


@router.message(AdminFSM.waiting_question)
async def admin_question_not_text(message: Message) -> None:
    await message.answer("Нужен текст — напишите формулировку вопроса.", reply_markup=cancel_keyboard())


@router.message(AdminFSM.waiting_answer, F.text)
async def admin_answer_chunk(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    parts: list[str] = list(data.get("answer_parts") or [])
    parts.append(message.text.strip())
    await state.update_data(answer_parts=parts)
    await message.answer(
        "Добавил. Можете прислать ещё текст или нажмите «Готово».",
        reply_markup=answer_collect_keyboard(),
    )


@router.message(AdminFSM.waiting_answer)
async def admin_answer_not_text(message: Message) -> None:
    await message.answer(
        "Пока принимаем только текст. Картинки добавим позже.",
        reply_markup=answer_collect_keyboard(),
    )


@router.callback_query(F.data == "dn", AdminFSM.waiting_answer)
async def admin_answer_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    parts: list[str] = list(data.get("answer_parts") or [])
    if not parts:
        await callback.answer("Сначала пришлите текст ответа", show_alert=True)
        return

    answer_html = "\n\n".join(user_text_to_html(part) for part in parts if part)
    await state.update_data(answer_html=answer_html)
    await state.set_state(AdminFSM.confirming)

    topic_title = data.get("topic_title") or "—"
    question_title = data.get("question_title") or "—"
    preview = (
        "Проверьте.\n\n"
        f"Тема: {escape_html(topic_title)}\n"
        f"Вопрос: {escape_html(question_title)}\n\n"
        f"Ответ:\n{_preview(answer_html)}"
    )
    await show_menu(callback, preview, confirm_keyboard())


@router.callback_query(F.data == "ok", AdminFSM.confirming)
async def admin_save(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    role_id = data.get("target_role_id")
    topic_id = data.get("topic_id")
    topic_title = data.get("topic_title")
    question_title = data.get("question_title")
    answer_html = data.get("answer_html")
    if not role_id or not topic_title or not question_title or not answer_html:
        await callback.answer("Данных не хватает, начните заново", show_alert=True)
        await state.clear()
        return

    if topic_id is None:
        topic_id = await db.create_topic(role_id, topic_title)

    await db.create_question(topic_id, question_title, answer_html)
    await state.clear()
    await show_menu(
        callback,
        "Сохранил. Вопрос уже виден в выбранной роли.\n\nМожно добавить ещё или сменить роль.",
        admin_roles_keyboard(),
    )
    await state.set_state(AdminFSM.choosing_topic)


@router.callback_query(F.data == "xx")
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_menu(callback, "Отменил. Выберите роль.", roles_keyboard())
