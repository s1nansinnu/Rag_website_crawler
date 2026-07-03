"""
HTML text extraction utilities.
returns clean text with metadata
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup

_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form"}

_MULTI_WHITESPACE = re.compile(r"\s+")

def extract (html:str, url: str) -> dict:
    """
    Extract clean text content from raw HTML.

    Parameters
    ----------
    html : str
        Raw HTML string.
    url : str
        The URL the HTML was fetched from (used in the returned metadata).

    Returns
    -------
    dict
        ``{ "url": str, "title": str, "text": str }``
    """
    soup= BeautifulSoup(html,"lxml")

#remove unwanted tags
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

#Extract title
    title_tag = soup.find("title")
    title= title_tag.get_text(strip=True) if title_tag else ""

    raw_text = soup.get_text(separator=" ", strip=True)
    clean_text  = _MULTI_WHITESPACE.sub(" ",raw_text).strip()

    return{
        "url":url,
        "title": title,
        "text": clean_text,
    }