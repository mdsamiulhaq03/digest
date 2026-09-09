from fastapi import FastAPI

from app.routes import documents, health

app = FastAPI(title="Digest")

app.include_router(health.router)
app.include_router(documents.router)
