import feedparser
from db import get_connection

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

def get_watchlist_isins():
    """Hakee kaikkien aktiivisten watchlist-yhtiöiden ISIN-koodit tietokannasta. """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, isin FROM companies WHERE is_active = true;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Palautetaan dict jossa avain on ISIN ja arvo on yhtiön id
    return {isin: company_id for company_id, isin in rows}

def save_announcement(company_id, data):
    """Tallentaa yhden tiedotteen announcements-tauluun. Ohittaa jos jo olemassa
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
    """
    INSERT INTO announcements (company_id, source, external_id, title, published_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (source, external_id) DO NOTHING
    RETURNING id;
    """,
    (company_id, "globenewswire", data["external_id"], data["title"], data["published"]),)

    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return result is not None # True jos uusi rivi lisättiin, False jos dedupe esti


if __name__ == "__main__":
    watchlist = get_watchlist_isins()
    print(f"Watchlistillä {len(watchlist)} yhtiötä")

    entries = fetch_feed()
    print(f"Löytyi {len(entries)} tiedotetta syötteestä")

    for entry in entries:
        data = extract_metadata(entry)

        if data["language"] != "fi":
            continue # Ohitetaan muunkieliset versiot samasta tiedotteesta

        company_id = watchlist.get(data["isin"])
        if company_id is None:
            continue # ei watchlistillä, ohitetaan

        was_new = save_announcement(company_id, data)
        status = "UUSI" if was_new else "jo olemassa"
        print(f"[{status}] {data['title']} (ISIN: {data['isin']})")