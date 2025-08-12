from pydantic import BaseModel
from pathlib import Path
import os

class Settings(BaseModel):
    # Default keeps your current repo layout
    MEMORY_ROOT: Path = Path(os.environ.get("MEMORY_ROOT", "ReactViewer/public/memory")).resolve()
    CORS_ALLOW_ORIGINS: str = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173")

    class Config:
        arbitrary_types_allowed = True

settings = Settings()
