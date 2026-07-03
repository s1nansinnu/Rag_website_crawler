"""
Playwright-based asynchronus BFS web crawler

"""
from __future__  import annotations

import asyncio
import logging
from collections import deque
from typing import AsyncGenerator, Callable, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from playwright.async_api import async_playwright, Route, Request

logger = logging.getLogger(__name__)

def normalise_url(url:str) -> str:
    """ Strip fragent and trailing slash for deduplication"""
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
        # RobotFileParser.read() is blocking; run in executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, rp.read)
    except Exception as exc:
        logger.warning("Could not fetch robots.txt from %s: %s", robots_url, exc)
        # If we can't read robots.txt, allow everything
        rp.allow_all = True
    return rp


def _is_same_domain(url: str, root_domain: str) -> bool:
    """Return True if *url* belongs to the same domain as *root_domain*."""
    try:
        return urlparse(url).netloc == root_domain
    except Exception:
        return False
    
#blocked for speed    
_BLOCKED_RESOURCE_TYPES = {"image", "font", "media", "stylesheet"}

async def crawl(
    root_url: str,
    max_pages: int = 50,
    crawl_delay: float = 1.0,
    progress_callback: Optional[Callable] = None,
) -> AsyncGenerator[dict, None]:
    """
    BFS-crawl *root_url* up to *max_pages* pages.

    Yields dicts with keys:
        pages_crawled (int), total_discovered (int),
        current_url (str), page_html (str)

    Parameters
    ----------
    root_url : str
        The starting URL.
    max_pages : int
        Maximum number of pages to visit.
    crawl_delay : float
        Seconds to wait between page loads.
    progress_callback : callable, optional
        An async callback ``(pages_crawled, total_discovered, current_url)``
        invoked after each page.
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

        # Block heavy resources
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
                if "text/html" not in content_type:
                    continue

                html = await page.content()
                pages_crawled += 1

                # Discover links
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

                total_discovered = len(visited) + len(queue)

                # Fire progress callback
                if progress_callback:
                    try:
                        await progress_callback(
                            pages_crawled, total_discovered, normalised
                        )
                    except Exception as cb_err:
                        logger.warning("Progress callback error: %s", cb_err)

                yield {
                    "pages_crawled": pages_crawled,
                    "total_discovered": total_discovered,
                    "current_url": normalised,
                    "page_html": html,
                }

                # Rate limit
                if crawl_delay > 0:
                    await asyncio.sleep(crawl_delay)

            except Exception as exc:
                logger.error("Error crawling %s: %s", normalised, exc)
                continue

        await browser.close()