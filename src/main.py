from collector import fetch_all_feeds, get_watchlist_isins, save_announcement, group_by_announcement
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
    """Hakee uudet tiedotteet kaikista syötteistä ja tallentaa ne tietokantaan."""
    watchlist = get_watchlist_isins()
    entries = fetch_all_feeds()
    announcements = group_by_announcement(entries, watchlist)

    new_count = 0
    for company_id, data in announcements:
        raw_content = fetch_full_text(data["link"])
        was_new = save_announcement(company_id, data, raw_content)
        if was_new:
            new_count += 1

    print(f"[Kerääjä] {new_count} uutta tiedotetta tallennettu.")


def run_summarizer():
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
    print(f"[Yhteenveto] {len(announcements)} yhteenvetoa tehty.")


async def run_notifier():
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
    run_summarizer()
    asyncio.run(run_notifier())
    print("--- Ajo valmis ---")