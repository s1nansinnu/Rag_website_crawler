"""
Playwright-based async BFS web crawler.
Falls back to httpx if Playwright is blocked.
Handles HTML, PDF, image and plain-text URLs.
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import AsyncGenerator, Callable, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from playwright.async_api import async_playwright, Route, Request

logger = logging.getLogger(__name__)

_BLOCKED_RESOURCE_TYPES = {"font", "media", "stylesheet"}
_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}

_HTTPX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


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


async def _httpx_fetch(url: str) -> tuple[str, str] | None:
    """
    Fallback fetch using httpx when Playwright is blocked.
    Returns (content_type, html) or None on failure.
    """
    try:
        async with httpx.AsyncClient(
            headers=_HTTPX_HEADERS,
            follow_redirects=True,
            timeout=20.0,
            verify=False,
        ) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None
            content_type = resp.headers.get("content-type", "text/html")
            return content_type, resp.text
    except Exception as exc:
        logger.warning("httpx fallback failed for %s: %s", url, exc)
        return None


async def crawl(
    root_url: str,
    max_pages: int = 10,
    crawl_delay: float = 1.0,
    progress_callback: Optional[Callable] = None,
) -> AsyncGenerator[dict, None]:
    """
    BFS-crawl root_url up to max_pages pages.
    Tries Playwright first; falls back to httpx if blocked.

    Yields dicts:
        pages_crawled, total_discovered, current_url, page_html
    """
    root_url = normalise_url(root_url)
    root_domain = urlparse(root_url).netloc
    robots = await _fetch_robots_parser(root_url)

    visited: set[str] = set()
    queue: deque[str] = deque([root_url])
    pages_crawled = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        )

        # Hide webdriver flag
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});"
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
            "window.chrome = { runtime: {} };"
        )

        async def _block_resources(route: Route, request: Request) -> None:
            if request.resource_type in _BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", _block_resources)
        page = await context.new_page()

        # Capture XHR/fetch API responses for JS-rendered job listings
        api_data: list[str] = []

        async def _capture_api(response):
            if "job" in response.url and response.status == 200:
                try:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        body = await response.json()
                        api_data.append(json.dumps(body))
                except Exception:
                    pass

        page.on("response", _capture_api)

        while queue and pages_crawled < max_pages:
            url = queue.popleft()
            normalised = normalise_url(url)

            if normalised in visited:
                continue

            if not getattr(robots, "allow_all", False):
                try:
                    if not robots.can_fetch("*", normalised):
                        logger.info("Blocked by robots.txt: %s", normalised)
                        continue
                except Exception:
                    pass

            visited.add(normalised)

            try:
                html = None
                content_type = "text/html"

                # ── Try Playwright first ──────────────────────────────────
                try:
                    response = await page.goto(
                        normalised,
                        wait_until="networkidle",
                        timeout=30_000,
                    )
                    if response and response.status < 400:
                        content_type = response.headers.get("content-type", "text/html")
                        page_type = _detect_type(content_type)

                        if page_type == "pdf":
                            raw_bytes = await response.body()
                            html = f'<pdf-binary data="{raw_bytes.hex()}" src="{normalised}"/>'
                        elif page_type == "image":
                            raw_bytes = await response.body()
                            mime = content_type.split(";")[0].strip()
                            html = f'<img-binary data="{raw_bytes.hex()}" mime="{mime}" src="{normalised}"/>'
                        elif page_type == "text":
                            raw_bytes = await response.body()
                            html = f'<plain-text src="{normalised}">{raw_bytes.decode("utf-8", errors="replace")}</plain-text>'
                        elif page_type == "html":
                            pw_html = await page.content()
                            # Append any captured API JSON as extra text
                        elif api_data:
                            html += "<api-data>" + " ".join(api_data) + "</api-data>"
                            # Check if page has meaningful content (not blank/blocked)
                            text_len = await page.evaluate("() => document.body?.innerText?.length || 0")
                            if text_len > 200:
                                html = pw_html
                            else:
                                logger.info("Playwright got blank page for %s, trying httpx", normalised)
                except Exception as pw_exc:
                    logger.warning("Playwright failed for %s: %s", normalised, pw_exc)

                # ── Fallback to httpx if Playwright got nothing ────────────
                if html is None:
                    logger.info("Using httpx fallback for %s", normalised)
                    result = await _httpx_fetch(normalised)
                    if result is None:
                        logger.warning("Both Playwright and httpx failed for %s", normalised)
                        continue
                    content_type, html = result
                    page_type = _detect_type(content_type)
                    if page_type not in ("html", "text"):
                        continue

                # ── Discover links from HTML ──────────────────────────────
                page_type = _detect_type(content_type)
                if page_type == "html":
                    try:
                        links = await page.eval_on_selector_all(
                            "a[href]",
                            "elements => elements.map(e => e.href)",
                        )
                    except Exception:
                        # If page context lost (httpx fallback), parse links from html
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, "lxml")
                        links = [
                            urljoin(normalised, a.get("href", ""))
                            for a in soup.find_all("a", href=True)
                        ]

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