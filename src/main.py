from collector import fetch_feed, extract_metadata, get_watchlist_isins, save_announcement
from content_fetcher import fetch_full_text
from summarizer import get_unsummarized_announcement, summarize_announcement, save_summaries
from notifier import get_unsent_summaries, format_message, mark_as_sent, send_message
from telegram import Bot
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def run_collector():
    """Hakee uudet tiedotteet ja tallentaa ne tietokantaan"""
    watchlist = get_watchlist_isins()
    entries = fetch_feed()

    new_count = 0
    for entry in entries:
        data = extract_metadata(entry)

        if data["language"] != "fi":
            continue
        
        company_id = watchlist.get(data["isin"])
        if company_id is None:
            continue

        raw_content = fetch_full_text(data["link"])
        was_new = save_announcement(company_id, data, raw_content)
        if was_new:
            new_count += 1

    print(f"[Kerääjä] {new_count} uutta tiedotetta tallennettu.")


def run_summarizer():
    """Tekee yhteenvedot tiedotteille joilla ei ole vielä sellaista."""

    announcements = get_unsummarized_announcement()

    for announcement_id, raw_content in announcements:
        summary_data = summarize_announcement(raw_content)
        save_summaries(announcement_id, summary_data)

    print(f"[Yhteenveto] {len(announcements)} yhteenvetoa tehty.")


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
    print("--- Ajo alkaa---")
    run_collector()
    run_summarizer()
    asyncio.run(run_notifier())
    print("--- Ajo valmis ---")
