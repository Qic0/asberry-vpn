# app/models/user.py Модель пользователя (SQLite)
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False
    )

    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)

    # 10 ₽ = 2 дня теста (5 ₽ / день)
    balance = Column(Integer, default=10)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

