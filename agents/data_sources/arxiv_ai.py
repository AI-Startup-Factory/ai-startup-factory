import feedparser


def fetch():

    signals = []

    feed = feedparser.parse(
        "https://export.arxiv.org/rss/cs.AI"
    )

    for e in feed.entries[:20]:

        signals.append({
            "source": "arxiv_ai",
            "title": e.title,
            "content": getattr(e, "summary", ""),
            "url": e.link,
            "score": 0
        })

    return signals
