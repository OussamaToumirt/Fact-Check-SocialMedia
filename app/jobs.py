from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from .config import settings
from .openai_pipeline import fact_check_transcript, transcribe_audio_mp3
from .schemas import Job
from .storage import read_json, write_json, write_model
from .ytdlp_audio import DownloadError, download_mp3


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    parts = urlsplit(url)
    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    filtered = []
    for k, v in query_pairs:
        kl = k.lower()
        if kl.startswith("utm_"):
            continue
        if kl in {"igshid", "fbclid"}:
            continue
        filtered.append((k, v))
    new_query = urlencode(filtered, doseq=True)
    normalized = urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            new_query,
            "",  # strip fragments
        )
    )
    return normalized


class JobStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.jobs_dir = base_dir / "jobs"
        self.index_path = base_dir / "url_index.json"
        self._lock = asyncio.Lock()
        self._jobs: Dict[str, Job] = {}
        self._index: Dict[str, str] = {}
        self._running: set[str] = set()

        data = read_json(self.index_path)
        if isinstance(data, dict):
            self._index = {str(k): str(v) for k, v in data.items()}

    def _job_dir(self, job_id: str) -> Path:
        return self.jobs_dir / job_id

    def _job_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _raw_response_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "openai_raw.json"

    def _transcript_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "transcript.txt"

    def _report_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "report.json"

    def _audio_dir(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "media"

    def _load_job_from_disk(self, job_id: str) -> Optional[Job]:
        data = read_json(self._job_path(job_id))
        if not data:
            return None
        try:
            return Job.model_validate(data)
        except Exception:
            return None

    @staticmethod
    def _cache_key(url: str, output_language: str) -> str:
        return f"{_normalize_url(url)}||{(output_language or '').strip().lower() or 'ar'}"

    async def find_or_create(self, *, url: str, output_language: str, force: bool = False) -> tuple[Job, bool]:
        async with self._lock:
            cache_key = self._cache_key(url, output_language)
            if not force:
                cached_id = self._index.get(cache_key)
                if cached_id:
                    job = self._jobs.get(cached_id) or self._load_job_from_disk(cached_id)
                    if job and job.status != "failed":
                        self._jobs[cached_id] = job
                        return job, True

            job_id = uuid4().hex
            now = datetime.now(tz=timezone.utc)
            job = Job(
                id=job_id,
                url=url,
                output_language=(output_language or "").strip().lower() or "ar",
                status="queued",
                created_at=now,
                updated_at=now,
                progress=0,
            )
            self._jobs[job_id] = job
            write_model(self._job_path(job_id), job)
            self._index[cache_key] = job_id
            write_json(self.index_path, self._index)
            return job, False

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]
        data = read_json(self._job_path(job_id))
        if not data:
            return None
        try:
            job = Job.model_validate(data)
        except Exception:
            return None
        async with self._lock:
            self._jobs[job_id] = job
        return job

    async def update(self, job_id: str, **fields) -> None:
        async with self._lock:
            job = self._jobs[job_id]
            updated = job.model_copy(update={**fields, "updated_at": datetime.now(tz=timezone.utc)})
            self._jobs[job_id] = updated
            write_model(self._job_path(job_id), updated)

    async def run_pipeline(self, job_id: str) -> None:
        async with self._lock:
            if job_id in self._running:
                return
            self._running.add(job_id)

        job = await self.get(job_id)
        if not job:
            async with self._lock:
                self._running.discard(job_id)
            return

        try:
            await self.update(job_id, status="downloading", progress=10, error=None)
            audio_dir = self._audio_dir(job_id)
            mp3_path = await asyncio.to_thread(
                download_mp3,
                url=job.url,
                out_dir=audio_dir,
                cookies_file=settings.ytdlp_cookies_file,
            )

            await self.update(job_id, status="transcribing", progress=40)
            transcript = await asyncio.to_thread(transcribe_audio_mp3, mp3_path)
            self._transcript_path(job_id).write_text(transcript, encoding="utf-8")

            await self.update(job_id, status="fact_checking", progress=70, transcript=transcript)
            report, raw = await asyncio.to_thread(
                fact_check_transcript,
                transcript=transcript,
                url=job.url,
                output_language=job.output_language,
            )
            write_model(self._report_path(job_id), report)
            write_json(self._raw_response_path(job_id), raw)

            await self.update(job_id, status="completed", progress=100, report=report)
        except DownloadError as e:
            await self.update(job_id, status="failed", progress=100, error=f"Download failed: {e}")
        except Exception as e:
            await self.update(job_id, status="failed", progress=100, error=str(e))
        finally:
            async with self._lock:
                self._running.discard(job_id)


job_store = JobStore(settings.data_dir)
