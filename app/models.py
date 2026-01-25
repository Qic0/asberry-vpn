from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    BigInteger,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)

    balance = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # 🔗 связь: один пользователь → много VPN
    vpn_clients = relationship(
        "VpnClient",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} balance={self.balance}>"


# =========================
# VPN CLIENT
# =========================
class VpnClient(Base):
    __tablename__ = "vpn_clients"

    id = Column(Integer, primary_key=True)

    # 🔗 владелец
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- X-UI ---
    xui_client_id = Column(String, unique=True, nullable=False)
    xui_email = Column(String, nullable=False)  # tg_123 / tg_123/1 / tg_123/2

    subscription_url = Column(String, nullable=False)

    # --- состояние ---
    active = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="vpn_clients",
    )

    def __repr__(self) -> str:
        return (
            f"<VpnClient email={self.xui_email} "
            f"active={self.active} user_id={self.user_id}>"
        )

