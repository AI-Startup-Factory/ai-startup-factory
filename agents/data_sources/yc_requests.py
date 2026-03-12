import feedparser


def fetch():

    signals = []

    feed = feedparser.parse(
        "https://www.ycombinator.com/blog/feed"
    )

    for e in feed.entries[:20]:

        signals.append({
            "source": "yc_blog",
            "title": e.title,
            "content": getattr(e, "summary", ""),
            "url": e.link,
            "score": 0
        })

    return signals
