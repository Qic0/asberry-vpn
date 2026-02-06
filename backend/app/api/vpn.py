from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.vpn import VPNDevice
from app.services.telegram_auth import verify_init_data
from app.services.xui import XUIService


router = APIRouter()

MAX_DEVICES = 15

xui = XUIService()


class CreateVPNPayload(BaseModel):
    name: str | None = None


class DeleteVPNPayload(BaseModel):
    device_id: int


@router.post("/create")
def create_vpn(payload: CreateVPNPayload, request: Request, db: Session = Depends(get_db)):
    """
    Создаёт VPN‑клиента в X‑UI и возвращает ссылку подключения.
    Telegram‑ID берём из заголовка `X-Telegram-Init-Data`.
    """
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="No initData header")

    try:
        tg_user = verify_init_data(init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    telegram_id = int(tg_user["id"])

    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=tg_user.get("first_name"),
            username=tg_user.get("username"),
            balance_rub=10,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if user.balance_rub < 5:
        raise HTTPException(400, "Недостаточно средств")

    devices_count = (
        db.query(VPNDevice)
        .filter(VPNDevice.user_id == user.id)
        .count()
    )

    if devices_count >= MAX_DEVICES:
        raise HTTPException(400, "Лимит устройств исчерпан")

    inbound_id = int(settings.XUI_INBOUND_ID)
    device_number = devices_count + 1
    display_name = payload.name or f"Устройство {device_number}"
    client_uuid, sub_id, vless_url, email = xui.create_client(
        inbound_id=inbound_id,
        telegram_id=telegram_id,
        device_number=device_number,
        name=display_name,
    )

    device = VPNDevice(
        user_id=user.id,
        telegram_id=telegram_id,
        xui_inbound_id=inbound_id,
        xui_client_uuid=client_uuid,
        xui_client_subid=sub_id,
        xui_client_email=email,
        name=display_name,
        device_index=device_number,
        enabled=True,
        price_per_day=5,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "device_id": device.id,
        "vless_url": vless_url,
    }


@router.post("/delete")
def delete_vpn(payload: DeleteVPNPayload, request: Request, db: Session = Depends(get_db)):
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="No initData header")

    try:
        tg_user = verify_init_data(init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    telegram_id = int(tg_user["id"])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    device = (
        db.query(VPNDevice)
        .filter(VPNDevice.user_id == user.id)
        .filter(VPNDevice.id == payload.device_id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    try:
        xui.delete_client(
            inbound_id=device.xui_inbound_id,
            client_uuid=device.xui_client_uuid,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка удаления в X-UI: {e}")

    db.delete(device)
    db.commit()
    return {"ok": True}


@router.get("/list")
def list_vpn(request: Request, db: Session = Depends(get_db)):
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="No initData header")

    try:
        tg_user = verify_init_data(init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    telegram_id = int(tg_user["id"])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {"items": []}

    devices = (
        db.query(VPNDevice)
        .filter(VPNDevice.user_id == user.id)
        .order_by(VPNDevice.device_index.asc())
        .all()
    )

    inbound_id = int(settings.XUI_INBOUND_ID)
    inbound = xui.get_inbound(inbound_id)
    clients_map = xui.get_clients_map(inbound_id)

    return {
        "items": [
            {
                "id": d.id,
                "name": d.name or f"Устройство {d.device_index}",
                "device_index": d.device_index,
                "enabled": bool(d.enabled),
                "price_per_day": d.price_per_day,
                "created_at": d.created_at,
                "vless_url": xui.build_vless_url(
                    client_uuid=d.xui_client_uuid,
                    email=d.xui_client_email or clients_map.get(d.xui_client_uuid) or f"tg_{telegram_id}",
                    inbound=inbound,
                    name=d.name or f"Устройство {d.device_index}",
                ),
            }
            for d in devices
        ]
    }
