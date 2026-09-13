import os
import json
import asyncio
from telegram import Bot
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RELEVANCE_EMOJI = {
    "high": "🔴",
    "medium": "🟡",
    "low": "⚪",
}

def get_unsent_summaries():
    """Hakee yhteenvedot joita ei ole vielä lähetetty Telegramiin"""

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT s.id, s.summary_text, a.title, a.link FROM summaries s JOIN announcements a ON a.id = s.announcement_id LEFT JOIN notifications n ON n.summary_id = s.id WHERE n.id IS NULL;""")

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def format_message(summary_data, link):
    """Muotoilee yhteenveto-JSON:in luettavaksi Telegram-viestiksi."""
    emoji = RELEVANCE_EMOJI.get(summary_data["relevance"], "⚪")

    msg = f"{emoji} <b>{summary_data['headline']}</b>\n\n"
    msg += f"{summary_data['summary']}\n\n"

    if summary_data.get("context"):
        msg += f"<i>Tausta:</i> {summary_dat['context']}\n\n"

    if summary_data.get("implications"):
        msg += f"<i>Merkitys:</i> {summary_data['implications']}\n\n"

    if summary_data.get("key_figures"):
        msg += f"📊 {summary_data['key_figures']}\n"

    if summary_data.get("outlook"):
        msg += f"📅 {summary_data['outlook']}\n"

    msg += f"\n🔗 <a href='{link}'>Lue tiedote</a>"

    return msg

def mark_as_sent(summary_id):
    """Merkitse yhteenvedon lähetetyksi notifications-tauluun. """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO notifications (summary_id, channel, status) VALUES (%s, %s, %s);", (summary_id, "telegram", "sent"),)

    conn.commit()
    cur.close()
    conn.close()

async def send_message(bot, text):
    """Lähettää yhden viestin Telegramiin."""

    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")

async def main():
    bot = Bot(token=BOT_TOKEN)
    summaries = get_unsent_summaries()
    print(f"Löytyi {len(summaries)} Lähettämätöntä yhteenvetoa.\n")

    for summary_id, summary_text, title, link in summaries:
        summary_data = json.loads(summary_text)
        message = format_message(summary_data, link)

        await send_message(bot, message)
        mark_as_sent(summary_id)

        print(f"Lähetetty: {summary_data['headline']}")

if __name__ == "__main__":
    asyncio.run(main())