"""Script per verificare i dati reali recuperati"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from io import StringIO

print("=" * 60)
print("VERIFICA DATI RECUPERATI")
print("=" * 60)
print()

# Verifica T. Rowe Price (ticker noto)
print("1. T. Rowe Price Health Sciences (PRHSX - ticker noto):")
try:
    ticker = yf.Ticker('PRHSX')
    hist = ticker.history(start=datetime.now() - timedelta(days=5*365), end=datetime.now())
    if not hist.empty:
        print(f"   Date disponibili: {hist.index[0].strftime('%d/%m/%Y')} - {hist.index[-1].strftime('%d/%m/%Y')}")
        print(f"   Numero record: {len(hist)}")
        print(f"   Primo prezzo: {hist['Close'].iloc[0]:.2f}")
        print(f"   Ultimo prezzo: {hist['Close'].iloc[-1]:.2f}")
        print(f"   Fonte: Yahoo Finance (ticker PRHSX)")
    else:
        print("   Nessun dato disponibile")
except Exception as e:
    print(f"   Errore: {e}")

print()

# Verifica un fondo europeo dalla cache
print("2. Alliance Bernstein (LU0097089360 - da cache):")
try:
    cache_file = 'cache/LU0097089360_historical.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        # Leggi i dati
        df = pd.read_json(StringIO(cached['data']), orient='records')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        
        if not df.empty:
            print(f"   Date disponibili: {df.index[0].strftime('%d/%m/%Y')} - {df.index[-1].strftime('%d/%m/%Y')}")
            print(f"   Numero record: {len(df)}")
            price_col = 'Price' if 'Price' in df.columns else df.columns[0]
            print(f"   Primo prezzo: {df[price_col].iloc[0]:.2f}")
            print(f"   Ultimo prezzo: {df[price_col].iloc[-1]:.2f}")
            print(f"   Fonte: Cache (recuperato da Yahoo Finance)")
            print(f"   Timestamp cache: {cached.get('timestamp', 'N/A')}")
        else:
            print("   Dati vuoti nella cache")
    else:
        print("   File cache non trovato")
except Exception as e:
    print(f"   Errore: {e}")

print()

# Verifica come Yahoo Finance trova i fondi europei
print("3. Test ricerca fondi europei su Yahoo Finance:")
test_isins = ["LU0097089360", "LU1960219225"]
for isin in test_isins:
    print(f"\n   Test ISIN: {isin}")
    found = False
    for exchange in ['L', 'PA', 'DE']:
        try:
            ticker_str = f"{isin}.{exchange}"
            stock = yf.Ticker(ticker_str)
            hist = stock.history(period="1mo")  # Prova con 1 mese
            if not hist.empty and len(hist) > 5:
                print(f"      ✓ Trovato con {ticker_str}")
                print(f"      Date: {hist.index[0].strftime('%d/%m/%Y')} - {hist.index[-1].strftime('%d/%m/%Y')}")
                found = True
                break
        except:
            continue
    if not found:
        print(f"      ✗ Non trovato su Yahoo Finance")

print()
print("=" * 60)
print("NOTA: Le date di partenza diverse dipendono da:")
print("  - Quando il fondo è stato quotato/tracciato su Yahoo Finance")
print("  - Disponibilità storica dei dati per quel fondo specifico")
print("  - Alcuni fondi potrebbero essere stati aggiunti a Yahoo Finance")
print("    in date diverse")
print("=" * 60)
