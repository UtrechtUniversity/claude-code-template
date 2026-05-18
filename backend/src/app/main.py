from fastapi import FastAPI

from app.routes.items import router as items_router

app = FastAPI(title="Template API")

app.include_router(items_router, prefix="/api/items")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
