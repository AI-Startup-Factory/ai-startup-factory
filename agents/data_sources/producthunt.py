import feedparser


def fetch():

    signals = []

    feed = feedparser.parse(
        "https://www.producthunt.com/feed"
    )

    for e in feed.entries[:20]:

        signals.append({
            "source": "producthunt",
            "title": e.title,
            "content": getattr(e, "summary", ""),
            "url": e.link,
            "score": 0
        })

    return signals
