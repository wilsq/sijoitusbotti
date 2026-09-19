import feedparser
from db import get_connection
from content_fetcher import fetch_full_text

FEED_URLS = {
    "Finland": "https://www.globenewswire.com/RssFeed/country/Finland/feedTitle/GlobeNewswire%20-%20News%20from%20Finland",
    "Sweden": "https://www.globenewswire.com/RssFeed/country/Sweden/feedTitle/GlobeNewswire%20-%20News%20from%20Sweden",
    "Norway": "https://www.globenewswire.com/RssFeed/country/Norway/feedTitle/GlobeNewswire%20-%20News%20from%20Norway",
}

# ISIN:n kaksi ensimmäistä kirjainta kertovat maan (ISO 3166-1 alpha-2).
# Tämän avulla tiedetään minkä kielinen versio tiedotteesta on ensisijainen.
PREFERRED_LANGUAGE_BY_ISIN_PREFIX = {
    "FI": "fi",
    "SE": "sv",
    "NO": "no",
}


def fetch_all_feeds():
    """Hakee kaikki maakohtaiset syötteet ja palauttaa yhdistetyn listan itemeistä."""
    all_entries = []
    for country, url in FEED_URLS.items():
        feed = feedparser.parse(url)
        all_entries.extend(feed.entries)
    return all_entries


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
        "link": entry.link,
        "language": entry.get("language"),
        "isin": isin,
        "ticker": ticker,
        "published": entry.published,
    }


def get_watchlist_isins():
    """Hakee kaikkien aktiivisten watchlist-yhtiöiden ISIN-koodit tietokannasta."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, isin FROM companies WHERE is_active = true AND isin IS NOT NULL;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {isin: company_id for company_id, isin in rows}


def pick_preferred_entry(versions, isin):
    """
    Sama tiedote voi esiintyä syötteessä useammalla kielellä.
    Valitaan yksi versio: ensisijaisesti yhtiön kotimaan kieli,
    toissijaisesti englanti, muuten ensimmäinen saatavilla oleva.
    """
    country_prefix = isin[:2] if isin else None
    preferred_lang = PREFERRED_LANGUAGE_BY_ISIN_PREFIX.get(country_prefix)

    for data in versions:
        if data["language"] == preferred_lang:
            return data

    for data in versions:
        if data["language"] == "en":
            return data

    return versions[0]


def group_by_announcement(entries, watchlist):
    """
    Suodattaa watchlistiin kuuluvat tiedotteet ja ryhmittelee
    saman tiedotteen kieliversiot yhteen (external_id:n perusteella).
    Palauttaa listan (company_id, data) -pareja, yksi per aito tiedote.
    """
    grouped = {}
    for entry in entries:
        data = extract_metadata(entry)

        if data["isin"] is None:
            continue

        company_id = watchlist.get(data["isin"])
        if company_id is None:
            continue  # ei watchlistillä

        key = data["external_id"]
        grouped.setdefault(key, []).append(data)

    result = []
    for external_id, versions in grouped.items():
        isin = versions[0]["isin"]
        company_id = watchlist[isin]
        chosen = pick_preferred_entry(versions, isin)
        result.append((company_id, chosen))

    return result


def save_announcement(company_id, data, raw_content):
    """Tallentaa yhden tiedotteen announcements-tauluun. Ohittaa jos jo olemassa (dedupe)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO announcements (company_id, source, external_id, title, link, raw_content, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, external_id) DO NOTHING
        RETURNING id;
        """,
        (company_id, "globenewswire", data["external_id"], data["title"], data["link"], raw_content, data["published"]),
    )
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return result is not None


if __name__ == "__main__":
    watchlist = get_watchlist_isins()
    print(f"Watchlistillä {len(watchlist)} yhtiötä.\n")

    entries = fetch_all_feeds()
    print(f"Löytyi yhteensä {len(entries)} tiedotetta kolmesta syötteestä.\n")

    announcements = group_by_announcement(entries, watchlist)
    print(f"Näistä watchlistiin kuuluvia, uniikkeja tiedotteita: {len(announcements)}\n")

    for company_id, data in announcements:
        raw_content = fetch_full_text(data["link"])
        was_new = save_announcement(company_id, data, raw_content)
        status = "UUSI" if was_new else "jo olemassa"
        content_status = f"{len(raw_content)} merkkiä" if raw_content else "EI SAATU"
        print(f"[{status}] {data['title']} (ISIN: {data['isin']}) — teksti: {content_status}")