import feedparser

FEED_URL = "https://www.globenewswire.com/RssFeed/country/Finland/feedTitle/GlobeNewswire%20-%20News%20from%20Finland"

def fetch_feed():

    """Hakee GlobeNewsWiren Suomi-syötteen ja palauttaa parsitut itemit"""
    feed = feedparser.parse(FEED_URL)
    return feed.entries

def extract_metadata(entry):
    """Poimii dc_identifier, ISIN ja tickerin yhdestä RSS-itemistä."""

    isin = None
    ticker = None
    for tag in entry.get("tags", []):
        if tag.get("scheme") == "https://www.globenewswire.com/rss/ISIN":
            isin = tag["term"]
        if tag.get("scheme") == "https://www.globenewswire.com/rss/stock":
            ticker = tag["term"]

    return {
        "external_id": entry.get("dc_identifier"),
        "title": entry.title,
        "summary": entry.summary,
        "link": entry.link,
        "language": entry.get("language"),
        "isin": isin,
        "ticker": ticker,
        "published": entry.published,
    }


if __name__ == "__main__":
    entries = fetch_feed()
 
 # Tutki vain suomenkieliset, joissa löytyy ISIN

    for entry in entries:
        data = extract_metadata(entry)
        if data["language"] == "fi" and data["isin"]:
            print(data)
            print("---")