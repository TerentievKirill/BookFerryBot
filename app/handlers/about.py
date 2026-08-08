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
        "ℹ️ BookFerry\n\n"
        "BookFerry помогает искать электронные книги и доставлять EPUB "
        "в Telegram и на электронную книгу по email.\n\n"
        "Для встроенных библиотек поиск выполняется по быстрому локальному "
        "индексу. При желании можно подключить собственный OPDS-каталог.\n\n"
        "Сами книги BookFerry постоянно не хранит: EPUB скачивается у "
        "источника только после выбора книги.\n\n"
        "Формат: EPUB\n"
        "Версия: 1.0\n\n"
        "Автор: Кирилл Т\n"
        "Email: kirillterentiev@gmail.com",
        reply_markup=ReplyKeyboardRemove(),
    )
