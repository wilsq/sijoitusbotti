import requests

HEADERS = { "User-Agent": "Sijoitusbotti wiljami@live.fi"}

CIK_MAP = {
    "AAPL": "0000320193",
    "BRK.B": "0001067983",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "ADC": "0000917251",
    "O": "0000726728",
    "KO": "0000021344",
}

RELEVANT_FORMS = {"8-K", "10-Q", "10-K"}

def fetch_recent_filings(cik):
    """ Hakee yhden yhtiön viimeisimmät SEC-tiedotteet"""

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
        
    for ticker, cik in CIK_MAP.items():
        data = fetch_recent_filings(cik)
        recent = data["filings"]["recent"]

        print(f"\n=== {ticker} ({data['name']}) ===")

        count = 0
        for i in range(len(recent["form"])):
            if recent["form"][i] in RELEVANT_FORMS:
                print(f"[{recent['form'][i]}] {recent['filingDate'][i]} - {recent['primaryDocument'][i]}")
                count += 1
                if count >= 3:
                    break
