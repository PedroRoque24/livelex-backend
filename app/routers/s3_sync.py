from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import ORJSONResponse
from pathlib import Path
import os, time, mimetypes

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception as e:
    boto3 = None

from ..utils.config import settings

router = APIRouter(tags=["s3"])

def _get_s3():
    if boto3 is None:
        raise HTTPException(status_code=500, detail="boto3 not available")
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        raise HTTPException(status_code=500, detail="S3_BUCKET not configured")
    region = os.environ.get("AWS_DEFAULT_REGION")
    s3 = boto3.client("s3", region_name=region) if region else boto3.client("s3")
    return s3, bucket

def _iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p

def _key_for(local_root: Path, file_path: Path, prefix: str = "memory/") -> str:
    rel = file_path.resolve().relative_to(local_root.resolve())
    key = f"{prefix}{str(rel).replace(os.sep, '/')}"
    return key

@router.get("/s3/status")
def s3_status():
    ok = True
    err = None
    bucket = os.environ.get("S3_BUCKET")
    try:
        if boto3 is None:
            raise RuntimeError("boto3 not available")
        s3, bucket_name = _get_s3()
        # simple check: head bucket
        s3.head_bucket(Bucket=bucket_name)
    except Exception as e:
        ok = False
        err = str(e)
    return ORJSONResponse({"ok": ok, "bucket": bucket, "memory_root": str(settings.MEMORY_ROOT), "error": err})

@router.post("/s3/backup")
def s3_backup():
    s3, bucket = _get_s3()
    root = settings.MEMORY_ROOT
    if not root.exists():
        raise HTTPException(status_code=400, detail=f"MEMORY_ROOT does not exist: {root}")

    count = 0
    t0 = time.time()
    for f in _iter_files(root):
        key = _key_for(root, f, prefix="memory/")
        ctype, _ = mimetypes.guess_type(str(f))
        extra = {"ContentType": ctype} if ctype else {}
        try:
            s3.upload_file(str(f), bucket, key, ExtraArgs=extra)
            count += 1
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Upload failed for {f}: {e}")
    dt = round(time.time() - t0, 3)
    return ORJSONResponse({"status": "ok", "uploaded": count, "seconds": dt, "bucket": bucket})

@router.post("/s3/restore")
def s3_restore(clear: bool = Query(False, description="Wipe local memory before restore")):
    s3, bucket = _get_s3()
    root = settings.MEMORY_ROOT
    root.mkdir(parents=True, exist_ok=True)

    if clear and root.exists():
        # Carefully remove only inside memory root
        for p in list(root.rglob("*"))[::-1]:
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    # remove empty dirs
                    try:
                        p.rmdir()
                    except OSError:
                        pass
            except Exception:
                pass

    # List objects with prefix memory/
    try:
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix="memory/")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"List failed: {e}")

    downloaded = 0
    t0 = time.time()
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            rel = key[len("memory/"):] if key.startswith("memory/") else key
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                s3.download_file(bucket, key, str(dest))
                downloaded += 1
            except ClientError as e:
                raise HTTPException(status_code=500, detail=f"Download failed for {key}: {e}")
    dt = round(time.time() - t0, 3)
    return ORJSONResponse({"status": "ok", "downloaded": downloaded, "seconds": dt, "bucket": bucket})

def maybe_autorestore():
    """Auto-restore on startup if MEMORY_ROOT is empty and S3 has data.
    Controlled by env AUTO_RESTORE_ON_STARTUP (default: '1').
    """
    if os.environ.get("AUTO_RESTORE_ON_STARTUP", "1") not in {"1", "true", "True"}:
        return
    root = settings.MEMORY_ROOT
    has_any = any(root.rglob("*")) if root.exists() else False
    if has_any:
        return
    try:
        s3, bucket = _get_s3()
        # probe if there is anything under memory/
        resp = s3.list_objects_v2(Bucket=bucket, Prefix="memory/", MaxKeys=1)
        if resp.get("KeyCount", 0) > 0:
            # pull
            _ = s3_restore.__wrapped__  # type: ignore
            # call underlying function without FastAPI wrapper (simulate default clear=False)
            s3_restore(clear=False)  # type: ignore
    except Exception as e:
        # best-effort; don't crash app start
        print(f"[S3] Auto-restore skipped: {e}")
