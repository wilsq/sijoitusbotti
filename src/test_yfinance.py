import yfinance as yf

import yfinance as yf

test_tickers = {
    "Kone (Helsinki)": "KNEBV.HE",
    "SSAB B (Tukholma)": "SSAB-B.ST",
    "Apple (USA)": "AAPL",
    "Berkshire B (USA)": "BRK-B",
    "Realty Income (USA)": "O",
}

for label, symbol in test_tickers.items():
    info = yf.Ticker(symbol).info
    pe = info.get("trailingPE")
    name = info.get("longName")
    print(f"{label} ({symbol}): {name} — P/E: {pe}")

# Poimitaan vain kiinnostavat kentät koko infon sijaan (info sisältää satoja kenttiä)
fields = {
    "P/E (trailing)": "trailingPE",
    "P/E (forward)": "forwardPE",
    "P/B": "priceToBook",
    "Osinkotuotto": "dividendYield",
    "Payout ratio": "payoutRatio",
    "EPS (trailing)": "trailingEps",
    "Liikevaihdon kasvu (YoY)": "revenueGrowth",
    "ROE": "returnOnEquity",
    "Debt/Equity": "debtToEquity",
    "Markkina-arvo": "marketCap",
}

print(f"--- {info.get('longName', 'Nokia')} ---\n")
for label, key in fields.items():
    value = info.get(key)
    print(f"{label}: {value}")