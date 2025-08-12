from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from .config import settings

MEM_ROOT = settings.MEMORY_ROOT

def within_root(p: Path) -> bool:
    try:
        p.resolve().relative_to(MEM_ROOT.resolve())
        return True
    except Exception:
        return False

def safe_path(rel_path: str) -> Path:
    p = (MEM_ROOT / rel_path).resolve()
    if not within_root(p):
        raise PermissionError("Path escapes memory root")
    return p

def list_files(glob: str = "**/*.json") -> List[str]:
    base = MEM_ROOT
    return sorted([str(p.relative_to(base)).replace("\\", "/") for p in base.glob(glob) if p.is_file()])

def list_patients() -> List[str]:
    p = MEM_ROOT / "patients"
    if not p.exists():
        return []
    out = []
    for child in p.iterdir():
        if child.is_dir():
            out.append(child.name)
    return sorted(out)

def list_cases(patient_id: str) -> List[str]:
    p = MEM_ROOT / "patients" / patient_id
    if not p.exists():
        return []
    out = []
    for child in p.iterdir():
        if child.is_dir():
            out.append(child.name)
    return sorted(out)
