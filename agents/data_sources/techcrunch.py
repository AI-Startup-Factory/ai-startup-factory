import feedparser


def fetch():

    signals = []

    feed = feedparser.parse(
        "https://techcrunch.com/feed/"
    )

    for e in feed.entries[:25]:

        signals.append({
            "source": "techcrunch",
            "title": e.title,
            "content": getattr(e, "summary", ""),
            "url": e.link,
            "score": 0
        })

    return signals
