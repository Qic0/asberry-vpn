# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.api.me import router as me_router

from app.api.vpn import router as vpn_router

from fastapi.staticfiles import StaticFiles

from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi import Request

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="/Asberry_vpn/frontend/static"),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)


app.include_router(me_router, prefix="/api")

app.include_router(vpn_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/miniapp", include_in_schema=False)
def miniapp():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)
