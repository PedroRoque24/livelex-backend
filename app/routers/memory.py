from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import ORJSONResponse, StreamingResponse
from pathlib import Path
import json, orjson

from ..utils.fs import safe_path, list_files, list_patients, list_cases
from ..models.schemas import FileList, Patients, Cases

router = APIRouter(tags=["memory"])

@router.get("/memory/{path:path}")
def get_memory_file(path: str):
    target = safe_path(path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Stream JSON safely; if not JSON, serve raw bytes
    suffix = target.suffix.lower()
    if suffix in (".json", ".jsonl"):
        def iter_bytes():
            with target.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    yield chunk
        media = "application/json" if suffix == ".json" else "application/x-ndjson"
        return StreamingResponse(iter_bytes(), media_type=media)
    else:
        # Fallback to raw
        return Response(content=target.read_bytes(), media_type="application/octet-stream")

@router.get("/list-files", response_model=FileList)
def list_files_api(glob: str = Query("**/*.json", description="Glob relative to memory root")):
    return ORJSONResponse({"files": list_files(glob)})

@router.get("/patients", response_model=Patients)
def patients_api():
    return ORJSONResponse({"patients": list_patients()})

@router.get("/cases/{patient_id}", response_model=Cases)
def cases_api(patient_id: str):
    return ORJSONResponse({"cases": list_cases(patient_id)})
