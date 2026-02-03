from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class VPNDevice(Base):
    __tablename__ = "vpn_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(Integer, index=True)

    xui_client_uuid = Column(Text, nullable=False)
    device_index = Column(Integer, nullable=False)

    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    disabled_at = Column(DateTime)

