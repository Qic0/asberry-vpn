import threading
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.models.vpn import VPNDevice
from app.services.xui import XUIService


PRICE_PER_DAY = 5


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


def run_billing_once() -> None:
    """
    Daily job:
    - for each user compute total_cost = active_devices * 5
    - if balance >= total_cost: charge
    - else: disable all active devices (DB + X-UI)
    """
    xui = XUIService()
    db: Session = SessionLocal()
    try:
        now = _utcnow()
        interval = timedelta(seconds=int(settings.BILLING_INTERVAL_SECONDS))
        users = db.query(User).all()
        for user in users:
            if user.last_billed_at and now - user.last_billed_at < interval:
                continue

            active_devices = (
                db.query(VPNDevice)
                .filter(VPNDevice.user_id == user.id)
                .filter(VPNDevice.enabled.is_(True))
                .all()
            )
            total_cost = len(active_devices) * PRICE_PER_DAY
            if total_cost <= 0:
                continue

            if user.balance_rub >= total_cost:
                user.balance_rub -= total_cost
                user.last_billed_at = now
                db.add(user)
                db.commit()
                continue

            # Not enough money: disable all active devices
            for d in active_devices:
                try:
                    xui.set_client_enabled(
                        inbound_id=d.xui_inbound_id,
                        client_uuid=d.xui_client_uuid,
                        enabled=False,
                    )
                except Exception:
                    # don't stop billing because one device failed to update in X-UI
                    pass

                d.enabled = False
                d.disabled_at = _utcnow()
                db.add(d)

            user.last_billed_at = now
            db.add(user)
            db.commit()
    finally:
        db.close()


def billing_loop() -> None:
    while True:
        try:
            run_billing_once()
        except Exception:
            # keep loop alive
            pass
        time.sleep(int(settings.BILLING_INTERVAL_SECONDS))


def start_billing_thread() -> None:
    if not settings.BILLING_ENABLED:
        return
    t = threading.Thread(target=billing_loop, daemon=True)
    t.start()
