"""Mock news API responses for NewsService testing."""
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def _load_articles():
    with open(GOLDEN_DIR / "news_articles.json") as f:
        return json.load(f)


def get_newsapi_response(query: str = "stock market", page_size: int = 10):
    """Mock NewsAPI response."""
    articles = _load_articles()[:page_size]
    return {
        "status": "ok",
        "totalResults": len(articles),
        "articles": [
            {
                "source": {"id": a.get("source", "test-source"), "name": a.get("source", "Test Source")},
                "title": a["title"],
                "description": a.get("description", ""),
                "url": a["url"],
                "publishedAt": a["published_at"],
                "content": a.get("description", ""),
            }
            for a in articles
        ]
    }


def get_rss_feed_xml(source: str = "yahoo"):
    """Return a minimal RSS XML feed for testing."""
    articles = _load_articles()[:5]
    items = ""
    for a in articles:
        items += f"""
        <item>
            <title>{a['title']}</title>
            <link>{a['url']}</link>
            <description>{a.get('description', '')}</description>
            <pubDate>{a['published_at']}</pubDate>
        </item>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test {source} Finance Feed</title>
        <link>https://test.{source}.com/rss</link>
        {items}
    </channel>
</rss>"""
