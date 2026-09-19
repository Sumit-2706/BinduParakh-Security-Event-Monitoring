"""
Fetches real, live cybersecurity news from The Hacker News' public RSS feed
and caches it in memory for a short time. This is genuine external data --
real headlines, real links to real articles -- not placeholder content.

Design choices, stated plainly:
- Uses Python's stdlib xml.etree instead of an extra RSS-parsing library,
  to avoid adding another third-party dependency for a fairly simple task.
- Caches results for CACHE_TTL_SECONDS so the dashboard doesn't hit the
  external feed on every single page load/poll.
- Fails gracefully: if the feed is unreachable (no internet, feed down),
  the app keeps working and simply returns an empty list rather than
  crashing the dashboard -- the same pattern used for the optional VPN
  detection rule.
"""
import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests

logger = logging.getLogger("binduparakh.news")

FEED_URL = "https://feeds.feedburner.com/TheHackersNews"
CACHE_TTL_SECONDS = 30 * 60  # 30 minutes
MAX_ITEMS = 12

_cache: Dict = {"items": [], "fetched_at": 0}


def _strip_namespaces(root: ET.Element) -> ET.Element:
    """Removes XML namespaces so <item>/<title>/<link> match predictably
    regardless of whether the feed declares a default namespace. Some
    RSS 2.0 feeds are namespace-free; others wrap items in a namespace
    that would make plain `.//item` queries return nothing."""
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def _parse_feed_xml(xml_bytes: bytes) -> List[dict]:
    """Parses RSS 2.0 XML bytes into a list of news items. Kept separate
    from the network fetch so it can be unit-tested without internet
    access -- feed a static sample and verify the parsing logic alone."""
    root = ET.fromstring(xml_bytes)
    _strip_namespaces(root)

    items = []
    for item in root.findall(".//item")[:MAX_ITEMS]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "published": pub_date,
            "source": "The Hacker News",
        })
    return items


def _fetch_and_parse() -> List[dict]:
    resp = requests.get(FEED_URL, timeout=8, headers={"User-Agent": "BinduParakh/1.0"})
    resp.raise_for_status()
    return _parse_feed_xml(resp.content)


def get_threat_news() -> List[dict]:
    """Returns cached news, refreshing from the live feed if the cache is
    stale. Never raises -- returns whatever it has (possibly empty) on
    any failure, since a broken news widget should never take down the
    rest of the dashboard."""
    now = time.time()
    # Serve whatever we have (even an empty list) until it goes stale, so a
    # down/unreachable feed is not re-hit on every single page load. The
    # "fetched_at" timestamp is set on failures too (see except branch).
    if now - _cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _cache["items"]

    try:
        items = _fetch_and_parse()
        _cache["items"] = items
        _cache["fetched_at"] = now
        logger.info("Refreshed threat news feed: %d items", len(items))
        return items
    except Exception as exc:  # noqa: BLE001
        # Negative-cache failures too: even an EMPTY first fetch gets a
        # "fetched_at" timestamp, otherwise a flaky/offline feed would be
        # re-hit on every single page load.
        _cache["fetched_at"] = now
        logger.warning("Could not refresh threat news feed: %s", exc)
        return _cache["items"]  # serve stale cache (possibly empty) rather than failing
