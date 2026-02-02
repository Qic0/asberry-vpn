from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔐 Мой VPN")],
        [KeyboardButton(text="💳 Баланс"), KeyboardButton(text="👥 Рефералы")],
        [KeyboardButton(text="🆘 Поддержка")],
    ],
    resize_keyboard=True
)

