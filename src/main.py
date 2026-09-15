from collector import fetch_feed, extract_metadata, get_watchlist_isins, save_announcement
from content_fetcher import fetch_full_text
from sumamrizer import get_unsent_summaries, format_message, mark_as_sent, send_message
from telegram import bot
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
