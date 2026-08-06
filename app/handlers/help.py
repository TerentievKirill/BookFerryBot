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
        "📚 Как пользоваться BookFerry\n\n"
        "1. Настройте бота командой /setting\n\n"
        "Нужно указать:\n\n"
        "• адрес OPDS-каталога;\n"
        "• email вашей электронной книги;\n"
        "• тему письма — по желанию.\n\n"
        "Можно указать до пяти email через запятую.\n\n"
        "2. Отправьте название книги обычным сообщением\n\n"
        "Например:\n\n"
        "Лабиринт отражений\n\n"
        "Бот покажет найденные книги. Для просмотра следующих "
        "результатов нажмите «Далее».\n\n"
        "3. Нажмите на нужную книгу\n\n"
        "Бот скачает книгу в формате EPUB, отправит её в Telegram "
        "и на указанные email.\n\n"
        "Если вы используете PocketBook, после первой отправки "
        "на почту вашего аккаунта придёт письмо с подтверждением. "
        "Добавьте адрес отправителя [адрес] в список доверенных "
        "отправителей Send-to-PocketBook — после этого книги будут "
        "поступать на устройство автоматически.\n\n"
        "Команды:\n\n"
        "/start — главное сообщение\n"
        "/setting — изменить настройки\n"
        "/profile — показать текущие настройки\n"
        "/help — открыть эту инструкцию\n"
        "/about — информация о проекте\n\n"
        "Команды /start, /setting, /profile, /help и /about "
        "прерывают незавершённое действие и возвращают бота "
        "в обычный режим.\n\n"
        "BookFerry специально оставлен простым: "
        "одна книга — одна кнопка — один EPUB.\n"
        "Для выбора других форматов и изданий используйте сайт "
        "OPDS-каталога.",
        reply_markup=ReplyKeyboardRemove(),
    )