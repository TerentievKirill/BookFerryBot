from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove


router = Router(name="about")


@router.message(Command("about"))
async def handle_about(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    await message.answer(
        "📚 BookFerry\n\n"
        "Бот для поиска книг в OPDS-каталогах и отправки "
        "на электронные книги.\n\n"
        "Формат книг: EPUB\n"
        "Версия: 1.0\n\n"
        "Автор: Кирилл Т\n"
        "Email: kirillterentiev@gmail.com\n\n"
        "Проект создан для удобной отправки книг "
        "на PocketBook и другие устройства.",
        reply_markup=ReplyKeyboardRemove(),
    )