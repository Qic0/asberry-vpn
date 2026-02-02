from fastapi import APIRouter, Header, HTTPException

from app.services.telegram_auth import verify_init_data

router = APIRouter(tags=["vpn"])


@router.get("/api/vpn/list")
def vpn_list(x_telegram_init_data: str = Header(...)):
    try:
        verify_init_data(x_telegram_init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    return []

