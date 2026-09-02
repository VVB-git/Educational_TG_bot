from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.auth import is_admin
from bot.db import Database
from bot.keyboards import roles_keyboard
from bot.roles import get_role
from bot.ui import show_menu

router = Router()

WELCOME = (
    "Привет! Это подсказки по работе — без команд, всё кнопками.\n\n"
    "Выберите роль."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=roles_keyboard())


@router.callback_query(F.data == "br")
async def back_to_roles(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_menu(callback, WELCOME, roles_keyboard())


@router.callback_query(F.data.startswith("role:"))
async def pick_role(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    role_id = callback.data.split(":", 1)[1]
    role = get_role(role_id)
    if role is None:
        await callback.answer("Такой роли нет", show_alert=True)
        return

    if role.kind == "admin":
        from bot.handlers.admin import open_admin

        if callback.from_user is None or not is_admin(callback.from_user.id):
            await callback.answer("Нет доступа к админке", show_alert=True)
            return
        await open_admin(callback, state)
        return

    from bot.handlers.reader import show_topics

    await state.clear()
    await show_topics(callback, db, role_id)
