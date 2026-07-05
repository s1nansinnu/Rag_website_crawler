"""
HTML text extraction utilities.
Handles HTML, PDF, images (OCR), and plain text.
Returns clean text with metadata.
"""
from __future__ import annotations

import io
import re
import logging
import json

from bs4 import BeautifulSoup
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form"}
_MULTI_WHITESPACE = re.compile(r"\s+")


def _extract_pdf(raw_bytes: bytes) -> str:
    """Extract all text from PDF bytes using pdfplumber."""
    parts = []
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text()
                if t:
                    parts.append(t)
    except Exception as exc:
        logger.warning("PDF extraction failed: %s", exc)
    return " ".join(parts)


def _extract_image(raw_bytes: bytes) -> str:
    """OCR text from image bytes using pytesseract."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        return pytesseract.image_to_string(img).strip()
    except Exception as exc:
        logger.warning("Image OCR failed: %s", exc)
        return ""


def _extract_html(html: str) -> tuple[str, str]:
    """Return (title, clean_text) from raw HTML string."""
    soup = BeautifulSoup(html, "lxml")

    # Remove unwanted tags
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    # Extract any injected API JSON data
    api_tag = soup.find("api-data")
    if api_tag:
        clean_text += " " + _MULTI_WHITESPACE.sub(" ", api_tag.get_text(" ", strip=True))
    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    raw_text = soup.get_text(separator=" ", strip=True)
    clean_text = _MULTI_WHITESPACE.sub(" ", raw_text).strip()
    return title, clean_text


def extract(html: str, url: str) -> dict:
    """
    Extract clean text from HTML, PDF, image, or plain-text content.

    Detects sentinel tags injected by spider.py for non-HTML content types.

    Parameters
    ----------
    html : str
        Raw HTML string or sentinel tag string from spider.py.
    url : str
        The URL the content was fetched from.

    Returns
    -------
    dict
        ``{ "url": str, "title": str, "text": str }``
    """
    # ── PDF sentinel ──────────────────────────────────────────────────────
    if html.startswith("<pdf-binary"):
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("pdf-binary")
        if tag and tag.get("data"):
            text = _extract_pdf(bytes.fromhex(tag["data"]))
        else:
            text = ""
        return {"url": url, "title": url.split("/")[-1], "text": text}

    # ── Image sentinel ────────────────────────────────────────────────────
    if html.startswith("<img-binary"):
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("img-binary")
        if tag and tag.get("data"):
            text = _extract_image(bytes.fromhex(tag["data"]))
        else:
            text = ""
        return {"url": url, "title": url.split("/")[-1], "text": text}

    # ── Plain text sentinel ───────────────────────────────────────────────
    if html.startswith("<plain-text"):
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("plain-text")
        text = tag.get_text(strip=True) if tag else ""
        clean_text = _MULTI_WHITESPACE.sub(" ", text).strip()
        return {"url": url, "title": url.split("/")[-1], "text": clean_text}
 
    # ── Normal HTML ───────────────────────────────────────────────────────
    title, clean_text = _extract_html(html)
    return {"url": url, "title": title, "text": clean_text}