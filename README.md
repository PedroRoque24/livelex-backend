# Livelex Backend (FastAPI)

Serves the React dashboard via an API instead of reading local `/memory/*.json` directly.
Designed for Railway/Render deployment; works locally too.

## Features
- `GET /api/health` — quick health check
- `GET /api/memory/{path}` — returns JSON file under memory root (safe, sandboxed)
- `GET /api/list-files` — glob search under memory root
- `GET /api/patients` — list patient IDs
- `GET /api/cases/{patient_id}` — list cases for a patient
- CORS enabled (configure allowed origins via env)
- Pluggable memory root (defaults to `ReactViewer/public/memory` so it matches your repo)
- Optional S3 backup script stub

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: point to your real memory folder (matches your layout)
set MEMORY_ROOT=ReactViewer/public/memory  # PowerShell: $env:MEMORY_ROOT="ReactViewer/public/memory"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Deploy on Railway
1. Create a new project, connect your repo.
2. Set environment variables (see `.env.example`).
3. Use **Procfile** (Railway auto-detect):
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Add a persistent volume and mount it at `/workspace/memory` if you plan to write files online.
5. Trigger a deploy; grab the public base URL.

## Frontend configuration
Set `VITE_API_URL` to your backend URL (e.g., `https://lex-backend.up.railway.app`).
Update all frontend fetches to call `${VITE_API_URL}/api/...`.

## Notes
- The API prevents directory traversal; paths are resolved and validated under MEMORY_ROOT.
- For large JSON files, responses are streamed.
- Add your ShadowBrain/loop processes in `app/loops/` later if you want them to run alongside the API.
