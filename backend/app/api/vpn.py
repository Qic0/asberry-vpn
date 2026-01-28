from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vpn import VPN
from app.models.user import User
from app.api.deps import get_current_user
from app.services.xui import login, create_vpn_client

router = APIRouter(prefix="/vpn", tags=["vpn"])


@router.get("/list")
def list_vpns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vpns = (
        db.query(VPN)
        .filter(VPN.user_id == user.id)
        .all()
    )

    return [
        {
            "id": vpn.id,
            "email": vpn.email,
            "vless_url": vpn.vless_url,
            "enabled": vpn.enabled,
        }
        for vpn in vpns
    ]


@router.post("/create")
def create_vpn(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. логинимся в x-ui
    try:
        login()
    except Exception:
        raise HTTPException(status_code=500, detail="x-ui login failed")

    # 2. создаём VPN в x-ui
    try:
        data = create_vpn_client(user.id)
    except Exception:
        raise HTTPException(status_code=500, detail="x-ui client creation failed")

    # 3. сохраняем в БД
    vpn = VPN(
        user_id=user.id,
        email=data["email"],
        vless_url=data["vless_url"],
        enabled=True,
    )

    db.add(vpn)
    db.commit()
    db.refresh(vpn)

    return {
        "id": vpn.id,
        "email": vpn.email,
        "vless_url": vpn.vless_url,
        "enabled": vpn.enabled,
    }

