from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="DocForge")


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok"}
