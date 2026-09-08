import feedparser

FEED_URL = "https://www.globenewswire.com/RssFeed/country/Finland/feedTitle/GlobeNewswire%20-%20News%20from%20Finland"

def fetch_feed():

    """Hakee GlobeNewsWiren Suomi-syötteen ja palauttaa parsitut itemit"""
    feed = feedparser.parse(FEED_URL)
    return feed.entries


if __name__ == "__main__":
    entries = fetch_feed()
    print(f"Löytyi {len(entries)} tiedostetta syötteestä.")

    for entry in entries:
        print(f"Otsikko: {entry.title}")
        print(f"Julkaistu: {entry.published}")
        print(f"Linkki: {entry.link}")
        print(f"Kentät saatavilla: {list(entry.keys())}")
        print("---")