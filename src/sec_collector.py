import requests
from datetime import datetime, timedelta
from db import get_connection
from content_fetcher import fetch_full_text

HEADERS = { "User-Agent": "Sijoitusbotti wiljami@live.fi"}


RELEVANT_FORMS = {"8-K", "10-Q", "10-K"}
LOOKBACK_DAYS = 7

def get_us_watchlist():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, cik FROM companies WHERE is_active = true AND cik IS NOT NULL;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows



def fetch_recent_filings(cik):
    """ Hakee yhden yhtiön viimeisimmät SEC-tiedotteet"""

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def build_document_url(cik, accession_number, primary_document):
    cik_no_zeros = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}/{primary_document}"

def save_announcement(company_id, title, link, accession_number, published_at, raw_content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO announcements (company_id, source, external_id, title, link, raw_content, published_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (source, external_id) DO NOTHING RETURNING id;""", (company_id, "sec_edgar", accession_number, title, link, raw_content, published_at),)

    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result is not None

if __name__ == "__main__":
    watchlist = get_us_watchlist()
    print(f"USA-Watchlistillä {len(watchlist)} yhtiöitä.\n")

    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    for company_id, cik in watchlist:
        data = fetch_recent_filings(cik)
        recent = data["filings"]["recent"]
        company_name = data["name"]

        for i in range(len(recent["form"])):
            form_type = recent["form"][i]
            if form_type not in RELEVANT_FORMS:
                continue

            filing_date_str = recent["filingDate"][i]
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")

            if filing_date < cutoff_date:
                break

            accession = recent["accessionNumber"][i]
            primary_doc = recent["primaryDocument"][i]
            doc_url = build_document_url(cik, accession, primary_doc)
            title = f"{company_name} - {form_type} ({filing_date_str})"

            raw_content = fetch_full_text(doc_url)
            was_new = save_announcement(company_id, title, doc_url, accession, filing_date_str, raw_content)

            status = "UUSI" if was_new else "jo olemassa"
            content_status = f"{len(raw_content)} merkkiä" if raw_content else "EI SAATU"
            print(f"[{status}] {title} - teksti: {content_status}")

