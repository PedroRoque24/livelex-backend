from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils.config import settings
from .routers import memory

app = FastAPI(title="Livelex Backend", version="1.0.0")

# CORS
allowed = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "memory_root": str(settings.MEMORY_ROOT)}

app.include_router(memory.router, prefix="/api")
