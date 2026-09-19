from collector import fetch_all_feeds, get_watchlist_isins, save_announcement, group_by_announcement
from sec_collector import get_us_watchlist, fetch_recent_filings, build_document_url, save_announcement as save_sec_announcement
from content_fetcher import fetch_full_text
from summarizer import get_unsummarized_announcement, summarize_announcement, save_summaries
from notifier import get_unsent_summaries, format_message, mark_as_sent, send_message
from telegram import Bot
import os
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

RELEVANT_FORMS = {"8-K", "10-Q", "10-K"}
LOOKBACK_DAYS = 7


def run_collector():
    """Hakee uudet tiedotteet GlobeNewswiren kolmesta maasta."""
    watchlist = get_watchlist_isins()
    entries = fetch_all_feeds()
    announcements = group_by_announcement(entries, watchlist)

    new_count = 0
    for company_id, data in announcements:
        raw_content = fetch_full_text(data["link"])
        was_new = save_announcement(company_id, data, raw_content)
        if was_new:
            new_count += 1

    print(f"[Kerääjä - GlobeNewswire] {new_count} uutta tiedotetta tallennettu.")


def run_sec_collector():
    """Hakee uudet tiedotteet SEC EDGARista USA-yhtiöille."""
    watchlist = get_us_watchlist()
    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    new_count = 0
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
            was_new = save_sec_announcement(company_id, title, doc_url, accession, filing_date_str, raw_content)
            if was_new:
                new_count += 1

    print(f"[Kerääjä - SEC EDGAR] {new_count} uutta tiedotetta tallennettu.")


def run_summarizer():
    """Tekee yhteenvedot tiedotteille joilla ei vielä ole sellaista."""
    announcements = get_unsummarized_announcement()

    success_count = 0
    for announcement_id, raw_content in announcements:
        try:
            summary_data = summarize_announcement(raw_content)
            save_summaries(announcement_id, summary_data)
            success_count += 1
        except Exception as e:
            print(f"[VIRHE] Tiedote id={announcement_id} epäonnistui: {e}")
            continue

    print(f"[Yhteenveto] {success_count}/{len(announcements)} yhteenvetoa tehty.")


async def run_notifier():
    """Lähettää lähettämättömät yhteenvedot Telegramiin."""
    bot = Bot(token=BOT_TOKEN)
    summaries = get_unsent_summaries()
    for summary_id, summary_text, title, link in summaries:
        summary_data = json.loads(summary_text)
        message = format_message(summary_data, link)
        await send_message(bot, message)
        mark_as_sent(summary_id)
    print(f"[Lähetys] {len(summaries)} viestiä lähetetty.")


if __name__ == "__main__":
    print("--- Ajo alkaa ---")
    run_collector()
    run_sec_collector()
    run_summarizer()
    asyncio.run(run_notifier())
    print("--- Ajo valmis ---")