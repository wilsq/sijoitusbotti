import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

PROMPT_TEMPLATE = """Olet sijoitustiedotteiden analyytikko. Tehtäväsi on lukea suomalaisen pörssiyhtiön 
tiedote ja tuottaa siitä kattava mutta jäsennelty yhteenveto JSON-muodossa. 
Tavoitteena on että lukija ymmärtää tapahtuman JA sen merkityksen ilman että 
hänen tarvitsee avata alkuperäistä tiedotetta.

TÄRKEÄÄ:
- Vastaa VAIN JSON-objektilla, ei mitään muuta tekstiä ennen tai jälkeen
- Jos tiedote ei mainitse jotain kenttää koskevaa tietoa, käytä arvoa null 
  äläkä arvaa tai päättele puuttuvaa tietoa
- "implications"-kentässä saat tulkita ja päätellä todennäköisiä vaikutuksia, 
  mutta merkitse selvästi jos kyse on omasta päättelystäsi eikä tiedotteen 
  suorasta sisällöstä (esim. "Tämä voisi tarkoittaa...")
- Kaikki tekstikentät kirjoitetaan suomeksi

Luokittele tiedotteen relevanssi (relevance) yhteen kolmesta tasosta:
- "high": tulosvaroitukset, ohjeistuksen muutokset, merkittävät yrityskaupat, 
  johdon vaihdokset (toimitusjohtaja/hallituksen puheenjohtaja)
- "medium": normaalit tulosjulkistukset, osavuosikatsaukset, isot sopimukset, 
  merkittävät strategiset avaukset
- "low": rutiini-ilmoitukset kuten omien osakkeiden ostot, pienet henkilöstömuutokset,
  yhtiökokouskutsut ilman poikkeuksellista sisältöä

Palauta JSON tässä muodossa:
{{
  "relevance": "high" | "medium" | "low",
  "event_type": "lyhyt tapahtumatyyppi, esim. earnings, guidance_change, buyback, management_change, product_launch",
  "headline": "lyhyt, iskevä otsikko suomeksi, max 6 sanaa",
  "summary": "3-4 lausetta: mitä tapahtui, keskeiset yksityiskohdat ja mahdolliset luvut.",
  "context": "1-2 lausetta: tausta tai syy tapahtumalle, jos tiedotteessa mainittu, muuten null",
  "implications": "2-3 lausetta: mitä tämä voisi tarkoittaa yhtiölle tai sijoittajalle.",
  "outlook": "1 lause: mahdollinen tulevaisuuden näkymä/ohjeistus, jos mainittu, muuten null",
  "key_figures": "keskeiset luvut lyhyesti, tai null jos ei numeerista dataa"
}}

Tiedote:
---
{content}
---
"""

PROMP_VERSION = "v1"

def summarize_announcement(raw_content):
    """Lähettää tiedotteen claudelle ja palauttaa jäsennellyn yhteenvedon dictinä. """

    prompt = PROMPT_TEMPLATE.format(content=raw_content)

    response = client.messages.create(model=MODEL, max_tokens=1000, messages=[{"role": "user", "content": prompt}],)

    response_text = response.content[0].text

# Poistetaan mahdolliset markdown-koodilohkomerkinnät (```json ... ```)
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]  # poista ensimmäinen rivi (```json)
        response_text = response_text.rsplit("```", 1)[0]  # poista viimeinen ```
        response_text = response_text.strip()

    return json.loads(response_text)


def get_unsummarized_announcement():
    """Hakee tiedotteet joilla ei ole vielä yhteenvetoa """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT a.id, a.raw_content FROM announcements a LEFT JOIN summaries s ON s.announcement_id = a.id WHERE s.id IS NULL AND a.raw_content IS NOT NULL;""")

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def save_summaries(announcement_id, summary_data):
    """ Tallentaa yhteenvedon summaries-tauluun"""

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO summaries (announcement_id, summary_text, relevance_level, event_type, model_used, prompt_version) VALUES (%s, %s, %s, %s, %s, %s);""", (announcement_id, json.dumps(summary_data, ensure_ascii=False), summary_data["relevance"], summary_data["event_type"], MODEL, PROMP_VERSION,),)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    announcements = get_unsummarized_announcement()
    print(f"Löytyi {len(announcements)} tiedotetta ilman yhteenvetoa\n")

    for announcement_id, raw_content in announcements:
        print(f"Käsitellään tiedote id={announcement_id}...")
        summary_data = summarize_announcement(raw_content)
        save_summaries(announcement_id, summary_data)
        print(f" -> {summary_data['headline']} ({summary_data['relevance']})")
