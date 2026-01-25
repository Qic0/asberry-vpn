import asyncio
from aiogram import Bot, Dispatcher
from app.config import settings
from app.bot.handlers import router

bot = Bot(token=settings.TG_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

