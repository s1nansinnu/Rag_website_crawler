"""
Pydantic request / response schemas for the API layer.
"""

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    """Body for the ``POST /api/crawl`` endpoint."""
    url: str = Field(..., description="Root URL to crawl")
    max_pages: int = Field(default=50, ge=1, le=500, description="Max pages to crawl")


class ChatRequest(BaseModel):
    """Body for the ``POST /api/chat`` endpoint."""
    question: str = Field(..., min_length=1, description="User question")
    session_id: str = Field(..., description="Session ID from a previous crawl")


class CrawlStatus(BaseModel):
    """Response model for crawl / index status."""
    status: str = Field(..., description="Current status (idle | crawling | indexing | ready | error)")
    pages_crawled: int = Field(default=0)
    total_chunks: int = Field(default=0)
