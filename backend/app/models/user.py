from sqlalchemy import Column, Integer, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Telegram — ВНЕШНИЙ идентификатор
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)

    balance = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

