import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)


# логирование всех сообщений пользователей
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if event.text:
            logging.info(f"User {event.from_user.id} sent: {event.text}")
        return await handler(event, data)


# команды бота в меню
async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="set_profile", description="Настроить профиль"),
        BotCommand(command="log_water", description="Добавить выпитую воду"),
        BotCommand(command="log_food", description="Записать прием пищи (текст/фото)"),
        BotCommand(command="log_workout", description="Записать тренировку"),
        BotCommand(command="check_progress", description="Показать прогресс и графики"),
    ]
    await bot.set_my_commands(commands)


# инициализация БД, запуск бота
async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(LoggingMiddleware())
    dp.include_router(router)

    await setup_bot_commands(bot)

    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())