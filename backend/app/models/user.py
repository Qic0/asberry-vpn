from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    balance_rub = Column(Integer, default=10, nullable=False)
    last_billed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    devices = relationship("VPNDevice", back_populates="user")
