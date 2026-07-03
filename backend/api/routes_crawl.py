"""
Crawl API routes.

Provides SSE-streamed crawl+ingest pipeline and a status endpoint.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.schemas import CrawlRequest, CrawlStatus
from crawler.spider import crawl
from crawler.extractor import extract
from rag.pipeline import ingest_documents, active_sessions
import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["crawl"])


async def _crawl_pipeline(
    url: str,
    max_pages: int,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """
    Run the full crawl → extract → ingest pipeline, yielding SSE events.

    Event types:
        progress   – { pages_crawled, total_discovered, current_url }
        chunking   – { message }
        embedding  – { progress_pct }
        complete   – { session_id, pages_crawled, total_chunks }
        error      – { message }
    """
    active_sessions[session_id] = {
        "status": "crawling",
        "pages_crawled": 0,
        "total_chunks": 0,
    }

    pages: list[dict] = []

    try:
        # ── Phase 1: Crawl ────────────────────────────────────────────────
        yield {
            "event": "progress",
            "data": json.dumps({
                "session_id": session_id,
                "pages_crawled": 0,
                "total_discovered": 1,
                "current_url": url,
                "phase": "crawling",
            }),
        }

        async for result in crawl(
            root_url=url,
            max_pages=max_pages,
            crawl_delay=config.CRAWL_DELAY,
        ):
            page_data = extract(result["page_html"], result["current_url"])
            pages.append(page_data)

            active_sessions[session_id]["pages_crawled"] = result["pages_crawled"]

            yield {
                "event": "progress",
                "data": json.dumps({
                    "session_id": session_id,
                    "pages_crawled": result["pages_crawled"],
                    "total_discovered": result["total_discovered"],
                    "current_url": result["current_url"],
                    "phase": "crawling",
                }),
            }

        if not pages:
            yield {
                "event": "error",
                "data": json.dumps({
                    "session_id": session_id,
                    "message": "No pages could be crawled from the provided URL.",
                }),
            }
            active_sessions[session_id]["status"] = "error"
            return

        # ── Phase 2: Chunk + Embed ────────────────────────────────────────
        yield {
            "event": "chunking",
            "data": json.dumps({
                "session_id": session_id,
                "message": f"Splitting {len(pages)} pages into chunks…",
            }),
        }

        async def _embedding_progress(phase: str, pct: float) -> None:
            """Tiny callback forwarded from pipeline.ingest_documents."""
            # We can't yield from a callback, so we just update session state.
            # The SSE events below handle the major phases.
            pass

        total_chunks = await ingest_documents(
            pages=pages,
            session_id=session_id,
            progress_callback=_embedding_progress,
        )

        yield {
            "event": "embedding",
            "data": json.dumps({
                "session_id": session_id,
                "progress_pct": 100.0,
            }),
        }

        # ── Phase 3: Complete ─────────────────────────────────────────────
        active_sessions[session_id]["status"] = "ready"
        active_sessions[session_id]["total_chunks"] = total_chunks

        yield {
            "event": "complete",
            "data": json.dumps({
                "session_id": session_id,
                "pages_crawled": len(pages),
                "total_chunks": total_chunks,
            }),
        }

    except Exception as exc:
        logger.exception("Crawl pipeline error for session %s", session_id)
        active_sessions[session_id]["status"] = "error"
        yield {
            "event": "error",
            "data": json.dumps({
                "session_id": session_id,
                "message": str(exc),
            }),
        }


@router.post("/crawl")
async def start_crawl(request: CrawlRequest):
    """
    Start a crawl+ingest pipeline and stream progress via SSE.

    Returns an ``EventSourceResponse`` with typed events.
    """
    session_id = str(uuid.uuid4())

    return EventSourceResponse(
        _crawl_pipeline(
            url=request.url,
            max_pages=request.max_pages,
            session_id=session_id,
        ),
        media_type="text/event-stream",
    )


@router.get("/status/{session_id}", response_model=CrawlStatus)
async def get_status(session_id: str):
    """Return the current crawl / index status for a session."""
    session = active_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return CrawlStatus(
        status=session.get("status", "unknown"),
        pages_crawled=session.get("pages_crawled", 0),
        total_chunks=session.get("total_chunks", 0),
    )
