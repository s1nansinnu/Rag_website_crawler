"""
LangChain RAG pipeline -- document ingestion and query.
Uses parallel batch embedding for minimal latency.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

import config
from rag.prompts import QA_PROMPT

logger = logging.getLogger(__name__)

# Tracks crawl / index status for each session_id.
active_sessions: dict[str, dict] = {}


def _index_path(session_id: str) -> Path:
    """Return the directory where a session's FAISS index is stored."""
    return config.FAISS_INDEX_DIR / session_id


async def _embed_batch(batch: list[Document], embeddings: GoogleGenerativeAIEmbeddings) -> FAISS:
    """Embed a single batch of documents in a thread."""
    return await asyncio.to_thread(FAISS.from_documents, batch, embeddings)


# -- Ingestion ----------------------------------------------------------------

async def ingest_documents(
    pages: list[dict],
    session_id: str,
    progress_callback: Optional[Callable] = None,
) -> int:
    """
    Convert crawled pages into a FAISS vector store and persist to disk.

    Parameters
    ----------
    pages : list[dict]
        Each dict must have ``url``, ``title``, and ``text`` keys.
    session_id : str
        Unique identifier for this crawl session.
    progress_callback : callable, optional
        ``async (phase: str, progress_pct: float) -> None``

    Returns
    -------
    int
        Total number of text chunks created.
    """
    active_sessions[session_id] = {
        "status": "chunking",
        "pages_crawled": len(pages),
        "total_chunks": 0,
    }

    # 1. Build LangChain Documents
    documents: list[Document] = []
    for page in pages:
        if not page.get("text"):
            continue
        documents.append(
            Document(
                page_content=page["text"],
                metadata={"source": page["url"], "title": page.get("title", "")},
            )
        )

    if not documents:
        active_sessions[session_id]["status"] = "error"
        raise ValueError("No text content extracted from crawled pages.")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    total_chunks = len(chunks)

    active_sessions[session_id]["total_chunks"] = total_chunks

    if progress_callback:
        try:
            await progress_callback("chunking", 100.0)
        except Exception:
            pass

    # 3. Create embeddings and FAISS index (parallel batches for low latency)
    active_sessions[session_id]["status"] = "embedding"

    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
    )

    batch_size = 100  # larger batches = fewer round trips

    if progress_callback:
        try:
            await progress_callback("embedding", 10.0)
        except Exception:
            pass

    # Build all batches and embed them in parallel
    batches = [chunks[i: i + batch_size] for i in range(0, total_chunks, batch_size)]
    results = await asyncio.gather(*[_embed_batch(b, embeddings) for b in batches])

    # Merge all batch vectorstores into one
    vectorstore = results[0]
    for vs in results[1:]:
        vectorstore.merge_from(vs)

    if progress_callback:
        try:
            await progress_callback("embedding", 100.0)
        except Exception:
            pass

    # 4. Persist to disk
    index_dir = _index_path(session_id)
    index_dir.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(vectorstore.save_local, str(index_dir))

    active_sessions[session_id]["status"] = "ready"
    logger.info(
        "Session %s: ingested %d pages -> %d chunks", session_id, len(pages), total_chunks
    )
    return total_chunks


# -- Query --------------------------------------------------------------------

async def query(
    question: str,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """
    Query the FAISS index for a session and stream answer tokens.

    Yields dicts:
        ``{"type": "token", "data": str}``
        ``{"type": "sources", "data": list[str]}``
        ``{"type": "done"}``
        ``{"type": "error", "data": str}``
    """
    index_dir = _index_path(session_id)

    if not index_dir.exists():
        yield {"type": "error", "data": f"No index found for session '{session_id}'. Please crawl a website first."}
        return

    # Load index
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
        )
        vectorstore = await asyncio.to_thread(
            FAISS.load_local,
            str(index_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        logger.error("Failed to load FAISS index for session %s: %s", session_id, exc)
        yield {"type": "error", "data": f"Failed to load index: {exc}"}
        return

    # Retrieve relevant documents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    try:
        relevant_docs = await asyncio.to_thread(retriever.invoke, question)
    except Exception as exc:
        logger.error("Retrieval failed: %s", exc)
        yield {"type": "error", "data": f"Retrieval error: {exc}"}
        return

    # Build context string
    context_parts: list[str] = []
    source_urls: list[str] = []
    for doc in relevant_docs:
        src = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", "")
        header = f"[Source: {src}]" + (f" (Title: {title})" if title else "")
        context_parts.append(f"{header}\n{doc.page_content}")
        if src not in source_urls:
            source_urls.append(src)

    context = "\n\n---\n\n".join(context_parts)

    # Build the LLM
    llm = ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
        temperature=0.3,
        streaming=True,
    )

    # Format the prompt
    formatted_prompt = QA_PROMPT.format(context=context, question=question)

    # Stream tokens
    try:
        async for chunk in llm.astream(formatted_prompt):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                yield {"type": "token", "data": token}
    except Exception as exc:
        logger.error("LLM streaming error: %s", exc)
        yield {"type": "error", "data": f"LLM error: {exc}"}
        return

    # Emit sources and done
    yield {"type": "sources", "data": source_urls}
    yield {"type": "done"}