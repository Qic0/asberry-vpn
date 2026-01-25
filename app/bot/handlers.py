from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import User
from app.services.vpn_service import XUIClient
from app.services.users import get_or_create_user

from aiogram.types import WebAppInfo


router = Router()

PRICE_PER_DAY = 5  # ₽


# ---------- КЛАВИАТУРА ----------
def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Мой VPN")],
            [
                KeyboardButton(text="💳 Баланс"),
                KeyboardButton(text="👥 Рефералы"),
            ],
            [
                KeyboardButton(
                    text="📱 Открыть VPN",
                    web_app=WebAppInfo(
                        url="https://dycani.ru:9443"  # <-- Mini App URL
                    ),
                )
            ],
            [KeyboardButton(text="🆘 Поддержка")],
        ],
        resize_keyboard=True,
    )


# ---------- /start ----------
@router.message(CommandStart())
async def start_handler(message: Message):
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session=session,
            telegram_id=str(message.from_user.id),
        )

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Все управление VPN теперь в приложении 👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📱 Перейти в приложение",
                        web_app=WebAppInfo(url="https://dycani.ru")
                    )
                ]
            ],
            resize_keyboard=True
        )
    )



@router.message(F.text == "🔐 Мой VPN")
async def my_vpn_handler(message: Message):
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        async with session.begin():  # DB transaction + lock
            result = await session.execute(
                select(User)
                .where(User.telegram_id == telegram_id)
                .with_for_update()
            )
            user = result.scalar_one_or_none()

            if not user:
                await message.answer("❌ Пользователь не найден. Напишите /start")
                return

            # 🆕 СОЗДАНИЕ VPN (ОДИН РАЗ)
            if not user.xui_client_id:
                xui = XUIClient()
                try:
                    client_id, vless_url = await xui.create_client(
                        email=f"tg_{telegram_id}"
                    )
                    user.xui_client_id = client_id
                    user.subscription_url = vless_url
                    user.subscription_active = False
                finally:
                    await xui.close()

            # 🔁 АВТОВКЛЮЧЕНИЕ
            if user.balance >= PRICE_PER_DAY and not user.subscription_active:
                xui = XUIClient()
                try:
                    await xui.enable_client(user.xui_client_id)
                    user.subscription_active = True
                finally:
                    await xui.close()

            # ✅ АКТИВЕН
            if user.subscription_active:
                await message.answer(
                    "🔐 **Ваш VPN**\n\n"
                    "✅ Подписка активна\n\n"
                    "🔗 **Ссылка:**\n"
                    f"`{user.subscription_url}`",
                    parse_mode="Markdown",
                )
                return

            # ❌ НЕ АКТИВЕН
            await message.answer(
                "🔒 Подписка не активна.\n"
                "Пополните баланс (≥ 5 ₽)."
            )







# ---------- БАЛАНС ----------
@router.message(F.text == "💳 Баланс")
async def balance_handler(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == str(message.from_user.id))
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        status = "Активен" if user.subscription_active else "Отключён"

        await message.answer(
            f"💳 **Баланс:** {user.balance} ₽\n"
            f"🔐 **VPN:** {status}",
            parse_mode="Markdown",
        )


# ---------- 🧪 ТЕСТ: ПОПОЛНЕНИЕ ----------
@router.message(F.text.startswith("/add_money"))
async def add_money_handler(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /add_money 50")
        return

    amount = int(parts[1])
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        user.balance += amount

        # 🔁 АВТОВКЛЮЧЕНИЕ VPN
        if user.xui_client_id and user.balance >= PRICE_PER_DAY:
            xui = XUIClient()
            try:
                await xui.enable_client(user.xui_client_id)
                user.subscription_active = True
            finally:
                await xui.close()

        await session.commit()

        await message.answer(
            f"✅ Баланс пополнен на {amount} ₽\n"
            f"💳 Текущий баланс: {user.balance} ₽"
        )


# ---------- 🧪 ТЕСТ: СПИСАНИЕ ----------
@router.message(F.text.startswith("/take_money"))
async def take_money_handler(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /take_money 5")
        return

    amount = int(parts[1])
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        user.balance = max(0, user.balance - amount)

        # 🔒 АВТООТКЛЮЧЕНИЕ VPN
        if user.xui_client_id and user.balance < PRICE_PER_DAY:
            xui = XUIClient()
            try:
                await xui.disable_client(user.xui_client_id)
                user.subscription_active = False
            finally:
                await xui.close()

        await session.commit()

        await message.answer(
            f"❌ Списано {amount} ₽\n"
            f"💳 Баланс: {user.balance} ₽"
        )


# ---------- РЕФЕРАЛЫ ----------
@router.message(F.text == "👥 Рефералы")
async def referral_handler(message: Message):
    await message.answer(
        "👥 **Реферальная программа**\n\n"
        "🎁 50 ₽ за каждого оплатившего пользователя",
        parse_mode="Markdown",
    )


# ---------- ПОДДЕРЖКА ----------
@router.message(F.text == "🆘 Поддержка")
async def support_handler(message: Message):
    await message.answer(
        "🆘 **Поддержка**\n\nНапишите администратору.",
        parse_mode="Markdown",
    )

