from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.me import router as me_router
from app.api.vpn import router as vpn_router
from app.database import Base, engine
from app.services.billing import start_billing_thread


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


@app.get("/")
def index():
    """
    Serve the main Mini App frontend.
    """
    print("SERVING INDEX FROM:", FRONTEND_DIR / "index.html")
    return FileResponse(FRONTEND_DIR / "index.html")


# ---------- API ROUTES ----------
app.include_router(me_router)
app.include_router(vpn_router, prefix="/api/vpn")


@app.on_event("startup")
def on_startup():
    # Ensure models are imported before create_all
    import app.models.user  # noqa: F401
    import app.models.vpn  # noqa: F401

    Base.metadata.create_all(bind=engine)
    start_billing_thread()

