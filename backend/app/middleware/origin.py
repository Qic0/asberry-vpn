from fastapi import Request, HTTPException

ALLOWED_ORIGINS = (
    "https://web.telegram.org",
    "https://t.me",
    "https://webappinternal.telegram.org",
)


async def check_origin(request: Request):
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin:
        if not any(origin.startswith(o) for o in ALLOWED_ORIGINS):
            raise HTTPException(status_code=403, detail="Invalid origin")

    if referer:
        if not any(referer.startswith(o) for o in ALLOWED_ORIGINS):
            raise HTTPException(status_code=403, detail="Invalid referer")

