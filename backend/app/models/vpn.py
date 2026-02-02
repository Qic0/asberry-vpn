from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class VPN(Base):
    __tablename__ = "vpns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, unique=True, nullable=False)
    vless_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

