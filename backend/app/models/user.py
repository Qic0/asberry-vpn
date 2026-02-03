from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    balance = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

