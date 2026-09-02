from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def show_menu(
    event: Message | CallbackQuery,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
        if message is None:
            return
        try:
            await message.edit_text(text, reply_markup=markup)
            return
        except TelegramBadRequest:
            await message.answer(text, reply_markup=markup)
        return
    await event.answer(text, reply_markup=markup)
