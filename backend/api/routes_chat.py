"""
Chat API routes.

Provides an SSE-streamed chat endpoint that queries the RAG pipeline.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from api.schemas import ChatRequest
from rag.pipeline import query, active_sessions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


async def _chat_stream(question: str, session_id: str) -> AsyncGenerator[dict, None]:
    """
    Stream chat response tokens via SSE.

    Event types:
        token   – { "text": str }
        sources – { "urls": list[str] }
        done    – {}
        error   – { "message": str }
    """
    # Check if session exists and is ready
    session = active_sessions.get(session_id)
    if session and session.get("status") not in ("ready",):
        yield {
            "event": "error",
            "data": json.dumps({
                "message": f"Session is not ready (status: {session.get('status', 'unknown')}). "
                           "Please wait for crawling to complete.",
            }),
        }
        return

    try:
        async for event in query(question=question, session_id=session_id):
            event_type = event.get("type")

            if event_type == "token":
                yield {
                    "event": "token",
                    "data": json.dumps({"text": event["data"]}),
                }
            elif event_type == "sources":
                yield {
                    "event": "sources",
                    "data": json.dumps({"urls": event["data"]}),
                }
            elif event_type == "done":
                yield {
                    "event": "done",
                    "data": json.dumps({}),
                }
            elif event_type == "error":
                yield {
                    "event": "error",
                    "data": json.dumps({"message": event["data"]}),
                }

    except Exception as exc:
        logger.exception("Chat stream error for session %s", session_id)
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc)}),
        }


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the crawled website content.

    Returns an ``EventSourceResponse`` streaming tokens, sources, and a done signal.
    """
    return EventSourceResponse(
        _chat_stream(
            question=request.question,
            session_id=request.session_id,
        ),
        media_type="text/event-stream",
    )
