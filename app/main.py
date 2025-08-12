from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils.config import settings
from .routers import memory, s3_sync, shadow_s3  # ← added shadow_s3

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
app.include_router(s3_sync.router, prefix="/api")
app.include_router(shadow_s3.router, prefix="/api")  # ← added include

@app.on_event("startup")
async def _startup_autorestore():
    try:
        s3_sync.maybe_autorestore()
    except Exception as e:
        print(f"[S3] startup restore skipped: {e}")
