# Sijoitusbotti

Python-pohjainen tekoälyavusteinen sovellus, joka seuraa pörssiyhtiöiden tiedotteita 
usealta markkinalta, tiivistää ne LLM:llä ja toimittaa yhteenvedot automaattisesti 
Telegramiin.

**Ongelma jonka ratkaisee:** aktiivisella sijoittajalla ei ole aikaa seurata kaikkia 
salkkunsa yhtiöiden tiedotteita manuaalisesti — botti suodattaa kohinan ja nostaa 
esiin vain relevantit tapahtumat.

## Ominaisuudet

- Kerää pörssitiedotteita GlobeNewswiren RSS-syötteistä (Suomi, Ruotsi, Norja) ja 
  SEC EDGAR -rajapinnasta (USA)
- Tunnistaa ja poimii monikielisistä tiedotejulkaisuista oikean kieliversion
- Tiivistää tiedotteet strukturoituun JSON-muotoon Claude-kielimallilla 
  (relevanssiluokittelu, tapahtumatyyppi, vaikutusanalyysi)
- Lähettää yhteenvedot Telegram-botin kautta, dedupetysti
- Ajastettu ajo GitHub Actionsin kautta

## Tekninen toteutus

- **Kieli/runtime:** Python
- **Tietokanta:** PostgreSQL (Neon)
- **AI:** Anthropic API (Claude)
- **Muut:** feedparser, trafilatura (tekstin poiminta ja siivous), python-telegram-bot
- **Infra:** GitHub Actions + ulkoinen ajastin, CI/CD-tyylinen automaatio

## Arkkitehtuuri

RSS/API-lähteet → tekstin haku & siivous → LLM-yhteenveto → Telegram <br>↓PostgreSQL (dedupe, historia)


## Teknisiä haasteita jotka ratkaistiin

- Monikielisten RSS-syötteiden yhdistäminen (sama tiedote useana kieliversiona)
- Luotettava deduplikointi usean datalähteen välillä
- LLM-vastausten strukturoitu jäsennys ja virhesietoisuus
- Ajastuksen luotettavuus (natiivi GitHub Actions -cron osoittautui epäluotettavaksi, 
  korvattiin ulkoisella laukaisijalla)
