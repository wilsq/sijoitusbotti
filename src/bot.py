import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Näyttää nykyisen watchlistin """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker, name, isin, cik FROM companies WHERE is_active = true ORDER BY ticker;")

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("Watchlist on tyhjä.")
        return

    lines = ["Watchlist:\n"]
    for ticker, name, isin, cik in rows:
        tunniste = f"ISIN: {isin}" if isin else f"CIK: {cik}"
        lines.append(f"• {ticker} - {name} ({tunniste})")

    await update.message.reply_text("\n".join(lines))

async def poista_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Poistaa yhtiön käytöstä tickerin perusteella """
    if not context.args:
        await update.message.reply_text("Käyttö: /poista Ticker\nEsim: /poista NOKIA")
        return

    ticker = context.args[0].upper()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE companies SET is_active = false WHERE UPPER(ticker) = %s RETURNING name;", (ticker,),)

    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if result:
        await update.message.reply_text(f"✅ {result[0]} ({ticker}) poistettu watchlistiltä.")
    else:
        await update.message.reply_text(f"❌ Tickeriä '{ticker}' ei löytynyt.")

async def lisaa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Lisää uuden yhtiön wathclistille. Käyttö: /lisaa isin TICKER "yhtiön nimi" ISIN_KOODI
    /lisaa cik TICKER "Yhtiön nimi" CIK_NUMERO"""
    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "Käyttö:\n"
            "/lisaa isin TICKER \"Yhtiön nimi\" ISIN_KOODI\n"
            "/lisaa cik TICKER \"Yhtiön nimi\" CIK_NUMERO\n\n"
            "Esim: /lisaa isin ELISA \"Elisa Oyj\" FI0009007884"
        )
        return

    tunniste_tyyppi = args[0].lower()
    ticker = args[1].upper()
    tunniste_arvo = args[-1]

    name = " ".join(args[2:-1]).strip('"')

    if tunniste_tyyppi not in ("isin", "cik"):
        await update.message.reply_text("Ensimmäisen parametrin pitää olla 'isin' tai 'cik'.")
        return
    
    conn = get_connection()
    cur = conn.cursor()

    if tunniste_tyyppi == "isin":
        cur.execute("""INSERT INTO companies (ticker, name, isin, is_active) VALUES (%s, %s, %s, true) ON CONFLICT (ticker) DO UPDATE SET is_active = true, isin = EXCLUDED.isin, name = EXCLUDED.name;""", (ticker, name, tunniste_arvo),)

    else:
        cur.execute(""" INSERT INTO companies (ticker, name, cik, is_active) VALUES (%s, %s, %s, true) ON CONFLICT (ticker) DO UPDATE SET is_active = true, cik = EXCLUDED.cik, name = EXCLUDED.name;""", (ticker, name, tunniste_arvo),)

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(f"✅ {name} ({ticker}) lisätty watchlistille.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tervetuloa Sijoitusbottiin!\n\n"
        "Komennot:\n"
        "/watchlist — näytä nykyinen lista\n"
        "/lisaa isin TICKER \"Nimi\" ISIN — lisää Pohjoismainen yhtiö\n"
        "/lisaa cik TICKER \"Nimi\" CIK — lisää USA-yhtiö\n"
        "/poista TICKER — poista yhtiö"
    )

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("poista", poista_command))
    app.add_handler(CommandHandler("lisaa", lisaa_command))

    print("Botti käynnissä, odottaa komentoja...")
    app.run_polling()