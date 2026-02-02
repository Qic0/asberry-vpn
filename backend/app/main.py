from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

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
    print("SERVING INDEX FROM:", FRONTEND_DIR / "index.html")
    return FileResponse(FRONTEND_DIR / "index.html")
