from fastapi import FastAPI

app = FastAPI(title="VPN Service API")

@app.get("/health")
async def health():
    return {"status": "ok"}

