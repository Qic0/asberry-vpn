from fastapi import APIRouter, Request, HTTPException
from app.services.telegram_auth import verify_init_data

router = APIRouter()


@router.get("/api/me")
async def me(request: Request):
    init_data = request.headers.get("X-Telegram-Init-Data")

    print("\n========== /api/me ==========")
    print("X-Telegram-Init-Data RAW:")
    print(init_data)
    print("================================\n")

    if not init_data:
        raise HTTPException(status_code=401, detail="No initData header")

    try:
        user = verify_init_data(init_data)
    except Exception as e:
        print("VERIFY ERROR:", repr(e))
        raise HTTPException(status_code=401, detail=str(e))

    return user

