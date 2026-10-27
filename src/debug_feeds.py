"""Diagnostiikka: näyttää mitä GlobeNewswiren syötteissä oikeasti on.
Ei kirjoita tietokantaan."""
import feedparser
from collections import Counter

from collector import FEED_URLS, get_watchlist_isins

ISIN_SCHEME = "https://www.globenewswire.com/rss/ISIN"
STOCK_SCHEME = "https://www.globenewswire.com/rss/stock"


def tags_of(entry, scheme):
    return [t["term"] for t in entry.get("tags", []) if t.get("scheme") == scheme]


if __name__ == "__main__":
    watchlist = get_watchlist_isins()
    seen_isins = Counter()

    for country, url in FEED_URLS.items():
        feed = feedparser.parse(url)
        entries = feed.entries
        print(f"\n=== {country} ===")
        print(f"HTTP-status: {feed.get('status')}, bozo: {feed.bozo}, "
              f"virhe: {feed.get('bozo_exception')}")
        print(f"Itemeitä: {len(entries)}")
        if not entries:
            continue

        print(f"Uusin: {entries[0].get('published')}")
        print(f"Vanhin: {entries[-1].get('published')}")

        with_isin = 0
        multi_isin = 0
        for e in entries:
            isins = tags_of(e, ISIN_SCHEME)
            stocks = tags_of(e, STOCK_SCHEME)
            if isins:
                with_isin += 1
            if len(isins) > 1:
                multi_isin += 1
            for i in isins:
                seen_isins[i] += 1
            mark = "*" if any(i in watchlist for i in isins) else " "
            print(f" {mark} ISIN={isins} stock={stocks} | {e.title[:60]}")

        print(f"ISIN-tagilla: {with_isin}/{len(entries)}, "
              f"useita ISINejä: {multi_isin}")

    print("\n=== Watchlist vs. syötteet ===")
    for isin, company_id in watchlist.items():
        print(f"{isin} (company_id {company_id}): "
              f"{'LÖYTYY syötteestä' if isin in seen_isins else 'ei syötteessä nyt'}")