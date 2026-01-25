from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)

    # ⬇⬇⬇ ВОТ ЭТО ДОБАВИТЬ ⬇⬇⬇
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    balance = Column(Integer, default=0)
    subscription_active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    vpn_clients = relationship(
        "VpnClient",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class VpnClient(Base):
    __tablename__ = "vpn_clients"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    xui_client_id = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)  # tg_123, tg_123/1 ...
    vless_url = Column(String, nullable=False)

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="vpn_clients")

    __table_args__ = (
        Index("ix_user_email", "user_id", "email"),
    )

