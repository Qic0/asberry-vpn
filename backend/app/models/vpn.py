from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class VPNDevice(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    telegram_id = Column(Integer, index=True, nullable=False)

    xui_inbound_id = Column(Integer, nullable=False)
    xui_client_uuid = Column(Text, nullable=False)
    xui_client_subid = Column(Text, nullable=False)
    xui_client_email = Column(String, nullable=True)

    name = Column(String, nullable=True)
    device_index = Column(Integer, nullable=False)

    enabled = Column(Boolean, default=True, nullable=False)
    price_per_day = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    disabled_at = Column(DateTime)

    user = relationship("User", back_populates="devices")
