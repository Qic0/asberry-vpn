from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.vpn import VPNDevice
from app.services.xui import XUIService

router = APIRouter()

PRICE_PER_DAY = 5
MAX_DEVICES = 15
INBOUND_ID = 2  # Reality inbound

xui = XUIService(
    base_url="https://xui.dycani.ru:31308",
    panel_path="xsYuxKzG2acQjiEbID",
    username="bW4ctc2eNl",
    password="hUVcAlcnTM",
)

@router.post("/create")
def create_vpn(telegram_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(telegram_id=telegram_id, balance=0)
        db.add(user)
        db.commit()
        db.refresh(user)

    if user.balance < PRICE_PER_DAY:
        raise HTTPException(400, "Недостаточно средств")

    devices_count = db.query(VPNDevice).filter(
        VPNDevice.user_id == user.id
    ).count()

    if devices_count >= MAX_DEVICES:
        raise HTTPException(400, "Лимит устройств исчерпан")

    client_uuid = xui.add_client(INBOUND_ID, telegram_id)

    device = VPNDevice(
        user_id=user.id,
        telegram_id=telegram_id,
        xui_client_uuid=client_uuid,
        device_index=devices_count + 1,
        enabled=1
    )

    db.add(device)
    db.commit()

    vless_url = f"vless://{client_uuid}@xui.dycani.ru:16034?type=tcp&security=reality"

    return {
        "device_id": device.id,
        "vless_url": vless_url
    }

