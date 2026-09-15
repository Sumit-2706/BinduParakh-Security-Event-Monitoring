"""
Tests the RSS parsing logic against a static, realistic sample -- modeled
on The Hacker News' actual feed structure -- without needing network
access. This is what CAN be verified offline; the live network fetch
itself can only be confirmed by running the app with real internet
access (this project's Docker container has it; this test sandbox does
not), so that part is deliberately not claimed as tested here.
"""
from app.news import _parse_feed_xml

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>The Hacker News</title>
  <link>https://thehackernews.com/</link>
  <item>
    <title>Microsoft Patches 398 Flaws Including a Windows Driver Zero-Day Under Active Attack</title>
    <link>https://thehackernews.com/2026/08/microsoft-patches-398-flaws-including.html</link>
    <pubDate>Tue, 11 Aug 2026 10:00:00 +0530</pubDate>
  </item>
  <item>
    <title>Sandworm-Linked UAC-0145 Uses Fake Job Interviews to Push VPN That Can Run Commands</title>
    <link>https://thehackernews.com/2026/08/sandworm-linked-uac-0145-uses-fake-job.html</link>
    <pubDate>Tue, 11 Aug 2026 08:12:00 +0530</pubDate>
  </item>
  <item>
    <title>Malformed item with no link</title>
    <pubDate>Tue, 11 Aug 2026 07:00:00 +0530</pubDate>
  </item>
</channel>
</rss>
"""


def test_parses_valid_items():
    items = _parse_feed_xml(SAMPLE_RSS)
    assert len(items) == 2  # the malformed (linkless) item must be skipped


def test_item_fields_are_populated():
    items = _parse_feed_xml(SAMPLE_RSS)
    first = items[0]
    assert first["title"].startswith("Microsoft Patches 398 Flaws")
    assert first["link"].startswith("https://thehackernews.com/")
    assert first["source"] == "The Hacker News"
    assert "2026" in first["published"]


def test_skips_items_missing_title_or_link():
    items = _parse_feed_xml(SAMPLE_RSS)
    titles = [i["title"] for i in items]
    assert "Malformed item with no link" not in titles


def test_empty_feed_returns_empty_list():
    empty_rss = b'<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    assert _parse_feed_xml(empty_rss) == []
