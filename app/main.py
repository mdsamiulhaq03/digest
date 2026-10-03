from fastapi import FastAPI

from app.routers import documents, health

app = FastAPI(title="Digest")

app.include_router(health.router)
app.include_router(documents.router)
