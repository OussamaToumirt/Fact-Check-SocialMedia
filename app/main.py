from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .jobs import job_store
from .schemas import AnalyzeRequest, HistoryItem, Job


app = FastAPI(title="Fact-Check Social Media", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    print(f"DEBUG: Received analyze request: {req.model_dump()}")
    
    api_key = req.api_key
    
    # Fallback to server keys if not provided
    if not api_key:
        if req.provider == "gemini":
            api_key = settings.gemini_api_key
        elif req.provider == "openai":
            api_key = settings.openai_api_key
        elif req.provider == "deepseek":
            api_key = settings.deepseek_api_key

    if not api_key:
        msg = f"{req.provider.title()} API key is required."
        if req.provider == "gemini":
            msg += " Get free key: https://aistudio.google.com/app/apikey"
        elif req.provider == "openai":
            msg += " Get key: https://platform.openai.com/api-keys"
        elif req.provider == "deepseek":
            msg += " Get key: https://platform.deepseek.com/api_keys"
        raise HTTPException(status_code=400, detail=msg)

    job, cached = await job_store.find_or_create(
        url=req.url, 
        output_language=req.output_language, 
        provider=req.provider,
        force=req.force, 
        api_key=api_key
    )
    
    if job.status not in {"completed", "failed"}:
        asyncio.create_task(job_store.run_pipeline(job.id, api_key=api_key))
    return {"job_id": job.id, "cached": cached}


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/history", response_model=list[HistoryItem])
async def history(limit: int = 50):
    return await job_store.list_history(limit=limit)
