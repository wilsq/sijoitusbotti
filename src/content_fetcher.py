import trafilatura
import requests

HEADERS = {"User-Agent": "Sijoitusbotti wiljami@live.fi"}

def fetch_full_text(url):
    """Hakee ja siivoaa tiedotteen koko tekstin annetusta URL:sta. Palauttaa None jos haku tai jäsennys epäonnistuu"""

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        downloaded = response.text
    except requests.RequestException:
        return None

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
    )
    return text

if __name__ == "__main__":
    # Testataan yhdellä oikealla linkillä
    test_url = "https://www.globenewswire.com/news-release/2026/09/08/3357425/0/fi/vaisala-tuo-markkinoille-datakeskuksille-r%C3%A4%C3%A4t%C3%A4l%C3%B6idyn-palvelukokonaisuuden.html"

    text = fetch_full_text(test_url)
    if text:
        print(F"Tekstin pituus: {len(text)} merkkiä")
        print(text)

    else:
        print("Tekstin haku epäonnistui.")
