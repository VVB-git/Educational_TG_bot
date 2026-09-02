from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.db import Database
from bot.keyboards import answer_keyboard, questions_keyboard, topics_keyboard
from bot.roles import get_role
from bot.text_format import escape_html, split_html
from bot.ui import show_menu

router = Router()


async def show_topics(event: Message | CallbackQuery, db: Database, role_id: str) -> None:
    role = get_role(role_id)
    title = escape_html(role.title if role else role_id)
    topics = await db.list_topics(role_id)
    if not topics:
        await show_menu(
            event,
            f"{title}\n\nПока нет тем. Их может добавить администратор.",
            topics_keyboard([], role_id),
        )
        return
    await show_menu(event, f"{title}\n\nВыберите тему.", topics_keyboard(topics, role_id))


async def show_questions(event: Message | CallbackQuery, db: Database, topic_id: int) -> None:
    topic = await db.get_topic(topic_id)
    if topic is None:
        if isinstance(event, CallbackQuery):
            await event.answer("Тема не найдена", show_alert=True)
        return
    questions = await db.list_questions(topic_id)
    topic_title = escape_html(topic["title"])
    if not questions:
        await show_menu(
            event,
            f"{topic_title}\n\nВ этой теме пока нет вопросов.",
            questions_keyboard([], topic["role_id"], topic_id),
        )
        return
    await show_menu(
        event,
        f"{topic_title}\n\nВыберите вопрос.",
        questions_keyboard(questions, topic["role_id"], topic_id),
    )


@router.callback_query(F.data.startswith("tp:"))
async def on_topic(callback: CallbackQuery, db: Database) -> None:
    topic_id = int(callback.data.split(":", 1)[1])
    await show_questions(callback, db, topic_id)


@router.callback_query(F.data.startswith("bt:"))
async def on_back_topics(callback: CallbackQuery, db: Database) -> None:
    role_id = callback.data.split(":", 1)[1]
    await show_topics(callback, db, role_id)


@router.callback_query(F.data.startswith("bq:"))
async def on_back_questions(callback: CallbackQuery, db: Database) -> None:
    topic_id = int(callback.data.split(":", 1)[1])
    await show_questions(callback, db, topic_id)


@router.callback_query(F.data.startswith("qs:"))
async def on_question(callback: CallbackQuery, db: Database) -> None:
    question_id = int(callback.data.split(":", 1)[1])
    question = await db.get_question(question_id)
    if question is None or callback.message is None:
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    await callback.answer()
    chunks = split_html(question["answer_html"])
    markup = answer_keyboard(question["role_id"], question["topic_id"])
    for i, chunk in enumerate(chunks):
        last = i == len(chunks) - 1
        await callback.message.answer(chunk, reply_markup=markup if last else None)
