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