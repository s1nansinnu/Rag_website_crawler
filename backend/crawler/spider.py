"""
Playwright-based async BFS web crawler.
Handles HTML, PDF, and image URLs.
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import AsyncGenerator, Callable, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from playwright.async_api import async_playwright, Route, Request

logger = logging.getLogger(__name__)

# Allow images + PDFs through; only block font/media/stylesheet
_BLOCKED_RESOURCE_TYPES = {"font", "media", "stylesheet"}

_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}


def normalise_url(url: str) -> str:
    """Strip fragment and trailing slash for deduplication."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


async def _fetch_robots_parser(root_url: str) -> RobotFileParser:
    """Download and parse robots.txt for the given root URL."""
    parsed = urlparse(root_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, rp.read)
    except Exception as exc:
        logger.warning("Could not fetch robots.txt from %s: %s", robots_url, exc)
        rp.allow_all = True
    return rp


def _is_same_domain(url: str, root_domain: str) -> bool:
    """Return True if url belongs to the same domain as root_domain."""
    try:
        return urlparse(url).netloc == root_domain
    except Exception:
        return False


def _detect_type(content_type: str) -> str:
    """Return 'html' | 'pdf' | 'image' | 'text' | 'unknown'."""
    ct = content_type.lower()
    if "text/html" in ct:
        return "html"
    if "application/pdf" in ct:
        return "pdf"
    if any(t in ct for t in _IMAGE_CONTENT_TYPES):
        return "image"
    if "text/plain" in ct:
        return "text"
    return "unknown"


async def crawl(
    root_url: str,
    max_pages: int = 10,
    crawl_delay: float = 1.0,
    progress_callback: Optional[Callable] = None,
) -> AsyncGenerator[dict, None]:
    """
    BFS-crawl root_url up to max_pages pages.

    Handles HTML, PDF, images, and plain text.
    Yields dicts: pages_crawled, total_discovered, current_url, page_html
    """
    root_url = normalise_url(root_url)
    root_domain = urlparse(root_url).netloc
    robots = await _fetch_robots_parser(root_url)

    visited: set[str] = set()
    queue: deque[str] = deque([root_url])
    pages_crawled = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        async def _block_resources(route: Route, request: Request) -> None:
            if request.resource_type in _BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", _block_resources)
        page = await context.new_page()

        while queue and pages_crawled < max_pages:
            url = queue.popleft()
            normalised = normalise_url(url)

            if normalised in visited:
                continue

            # Respect robots.txt
            if not getattr(robots, "allow_all", False):
                try:
                    if not robots.can_fetch("*", normalised):
                        logger.info("Blocked by robots.txt: %s", normalised)
                        continue
                except Exception:
                    pass

            visited.add(normalised)

            try:
                response = await page.goto(
                    normalised,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                if response is None or response.status >= 400:
                    logger.warning(
                        "Skipping %s (status=%s)",
                        normalised,
                        response.status if response else "no response",
                    )
                    continue

                content_type = response.headers.get("content-type", "")
                page_type = _detect_type(content_type)

                # Skip completely unknown types (e.g. zip, exe)
                if page_type == "unknown":
                    logger.debug("Skipping unsupported content-type %s at %s", content_type, normalised)
                    continue

                # ── PDF ──────────────────────────────────────────────────
                if page_type == "pdf":
                    raw_bytes = await response.body()
                    html = f'<pdf-binary data="{raw_bytes.hex()}" src="{normalised}"/>'

                # ── Image ────────────────────────────────────────────────
                elif page_type == "image":
                    raw_bytes = await response.body()
                    mime = content_type.split(";")[0].strip()
                    html = f'<img-binary data="{raw_bytes.hex()}" mime="{mime}" src="{normalised}"/>'

                # ── Plain text ───────────────────────────────────────────
                elif page_type == "text":
                    raw_bytes = await response.body()
                    html = f'<plain-text src="{normalised}">{raw_bytes.decode("utf-8", errors="replace")}</plain-text>'

                # ── HTML (default) ───────────────────────────────────────
                else:
                    html = await page.content()

                    # Discover links only from HTML pages
                    links = await page.eval_on_selector_all(
                        "a[href]",
                        "elements => elements.map(e => e.href)",
                    )
                    for link in links:
                        abs_link = urljoin(normalised, link)
                        norm_link = normalise_url(abs_link)
                        if (
                            norm_link not in visited
                            and _is_same_domain(norm_link, root_domain)
                            and urlparse(norm_link).scheme in ("http", "https")
                        ):
                            queue.append(norm_link)

                pages_crawled += 1
                total_discovered = len(visited) + len(queue)

                if progress_callback:
                    try:
                        await progress_callback(pages_crawled, total_discovered, normalised)
                    except Exception as cb_err:
                        logger.warning("Progress callback error: %s", cb_err)

                yield {
                    "pages_crawled": pages_crawled,
                    "total_discovered": total_discovered,
                    "current_url": normalised,
                    "page_html": html,
                }

                if crawl_delay > 0:
                    await asyncio.sleep(crawl_delay)

            except Exception as exc:
                logger.error("Error crawling %s: %s", normalised, exc)
                continue

        await browser.close()