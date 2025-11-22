"""Utilities for retrieving article bodies when available."""

from __future__ import annotations

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import Config
from .models import Article

LOGGER = logging.getLogger(__name__)


@retry(
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def _fetch_article_html(url: str, timeout: int) -> requests.Response:
    """Fetch article HTML with retry logic."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def enrich_article_content(article: Article, config: Config) -> Article:
    """Attempt to populate the article's content by scraping the linked page.

    If scraping fails the original article is returned unchanged.
    """

    if article.content:
        return article

    try:
        response = _fetch_article_html(article.url, config.request_timeout)
    except requests.RequestException as exc:
        LOGGER.debug("Unable to fetch article body for %s: %s", article.url, exc)
        return article

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.select("p") if p.get_text(strip=True)]
    if not paragraphs:
        return article

    text = "\n\n".join(paragraphs)
    if len(text) > config.max_content_chars:
        text = text[:config.max_content_chars]
    article.content = text
    return article


def best_text(article: Article, config: Config) -> Optional[str]:
    """Return the most suitable text for summarization."""

    enriched = enrich_article_content(article, config)
    return enriched.primary_text()
