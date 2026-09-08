import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Palauttaa yhteyden Neon-Postgres tietokantaan .env:ssä määritetyllä osoitteella."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL puuttuu .env-tiedostosta")
    return psycopg2.connect(database_url)

if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, ticker, name FROM companies")
    rows = cur.fetchall()

    if rows:
        print(f"Yhteys toimii! Löytyi {len(rows)} yhtiöitä:")
        for row in rows:
            print(f" - {row}")
    else:
        print(f"Yhteys toimii, mutta companies-taulu on tyhjä.")

        cur.close()
        conn.close()

