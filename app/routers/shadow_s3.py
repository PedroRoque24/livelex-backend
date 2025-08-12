import os, shutil
from pathlib import Path
from fastapi import APIRouter, Query
import boto3

router = APIRouter()

# Environment variables (already set for your normal S3 backup)
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")

# Where the shadow_memory lives in the container
SHADOW_ROOT = Path("/workspace/shadow_memory")
S3_PREFIX = "shadow_memory"

def s3_client():
    return boto3.client("s3", region_name=AWS_REGION)

@router.post("/api/s3/backup-shadow")
def backup_shadow():
    """Back up shadow_memory to S3."""
    if not SHADOW_ROOT.exists():
        return {"status": "ok", "uploaded": 0, "note": f"{SHADOW_ROOT} does not exist"}
    s3 = s3_client()
    count = 0
    for p in SHADOW_ROOT.rglob("*"):
        if p.is_file():
            key = f"{S3_PREFIX}/{p.relative_to(SHADOW_ROOT).as_posix()}"
            s3.upload_file(str(p), S3_BUCKET, key)
            count += 1
    return {"status": "ok", "uploaded": count, "prefix": S3_PREFIX}

@router.post("/api/s3/restore-shadow")
def restore_shadow(clear: bool = Query(True, description="Clear before restore")):
    """Restore shadow_memory from S3."""
    s3 = s3_client()
    if clear and SHADOW_ROOT.exists():
        shutil.rmtree(SHADOW_ROOT)
    SHADOW_ROOT.mkdir(parents=True, exist_ok=True)

    paginator = s3.get_paginator("list_objects_v2")
    total = 0
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f"{S3_PREFIX}/"):
        for obj in page.get("Contents", []):
            rel = obj["Key"][len(S3_PREFIX)+1:]
            if not rel:
                continue
            dst = SHADOW_ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(S3_BUCKET, obj["Key"], str(dst))
            total += 1
    return {"status": "ok", "downloaded": total, "prefix": S3_PREFIX, "cleared": clear}
