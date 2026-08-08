from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove


router = Router(name="help")


@router.message(Command("help"))
async def handle_help(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    await message.answer(
        "❓ Как пользоваться BookFerry\n\n"
        "1. Если запускаете бота впервые, откройте Menu рядом с полем "
        "ввода и выберите «Мастер настройки».\n\n"
        "Мастер попросит выбрать библиотеку, указать email электронной "
        "книги и при желании тему письма.\n\n"
        "2. Для поиска просто отправьте название или автора книги "
        "обычным сообщением.\n\n"
        "Бот покажет найденные книги. Нажмите на нужную — EPUB будет "
        "отправлен в Telegram и на настроенные email.\n\n"
        "3. Чтобы быстро сменить библиотеку, откройте "
        "Menu → «Сменить каталог». Email и тема при этом не меняются.\n\n"
        "В Menu также доступны:\n"
        "• Мастер настройки — пройти настройку заново;\n"
        "• Сменить каталог — выбрать другую библиотеку;\n"
        "• Профиль — посмотреть текущие параметры;\n"
        "• Помощь — открыть эту инструкцию;\n"
        "• О проекте — информация о BookFerry.\n\n"
        "Если нужной библиотеки нет в списке, выберите «Другой OPDS» "
        "и отправьте её OPDS-адрес.\n\n"
        "Для PocketBook: после первой отправки может прийти письмо с "
        "подтверждением. Добавьте отправителя BookFerry в доверенные "
        "отправители Send-to-PocketBook.\n\n"
        "BookFerry работает с EPUB: одна книга — одна кнопка — один файл.",
        reply_markup=ReplyKeyboardRemove(),
    )
