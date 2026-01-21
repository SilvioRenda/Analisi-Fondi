"""Script per testare il recupero dati di Polar Capital"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

isin = 'IE00BKSBD728'
print("=" * 70)
print(f"TEST RECUPERO DATI POLAR CAPITAL")
print(f"ISIN: {isin}")
print("=" * 70)
print()

# Test 1: Exchange codes
print("1. Test con Exchange Codes:")
print("-" * 70)
exchanges = ['L', 'PA', 'DE', 'MI', 'AS', 'SW', 'BR', 'VI', 'IR', 'LN', 'LS']
found = False

for ex in exchanges:
    try:
        ticker_str = f"{isin}.{ex}"
        print(f"   Provo {ticker_str}...", end=" ")
        stock = yf.Ticker(ticker_str)
        hist = stock.history(period='1y')
        if not hist.empty and len(hist) > 10:
            print(f"✓ TROVATO!")
            print(f"   Date: {hist.index[0].strftime('%d/%m/%Y')} - {hist.index[-1].strftime('%d/%m/%Y')}")
            print(f"   Record: {len(hist)}")
            print(f"   Primo prezzo: {hist['Close'].iloc[0]:.2f}")
            print(f"   Ultimo prezzo: {hist['Close'].iloc[-1]:.2f}")
            found = True
            break
        else:
            print("vuoto")
    except Exception as e:
        print(f"errore: {str(e)[:50]}")

if not found:
    print("   X Nessun dato trovato con exchange codes")
print()

# Test 2: ISIN diretto
print("2. Test con ISIN diretto:")
print("-" * 70)
try:
    print(f"   Provo {isin}...", end=" ")
    stock = yf.Ticker(isin)
    hist = stock.history(period='1y')
    if not hist.empty and len(hist) > 10:
        print(f"✓ TROVATO!")
        print(f"   Date: {hist.index[0].strftime('%d/%m/%Y')} - {hist.index[-1].strftime('%d/%m/%Y')}")
        print(f"   Record: {len(hist)}")
        found = True
    else:
        print("vuoto")
except Exception as e:
    print(f"errore: {str(e)[:50]}")

if not found:
    print("   X Nessun dato trovato con ISIN diretto")
print()

# Test 3: Info del ticker (se esiste)
print("3. Test info ticker (se disponibile):")
print("-" * 70)
for ex in ['L', 'IR', 'LN']:
    try:
        ticker_str = f"{isin}.{ex}"
        stock = yf.Ticker(ticker_str)
        info = stock.info
        if info and len(info) > 5:
            print(f"   {ticker_str}: Info disponibili")
            print(f"   Nome: {info.get('longName', 'N/A')}")
            print(f"   Simbolo: {info.get('symbol', 'N/A')}")
            break
    except:
        continue
print()

# Test 4: Prova con nome alternativo
print("4. Ricerca alternativa:")
print("-" * 70)
print("   Provo a cercare 'Polar Capital Healthcare' su Yahoo Finance...")
try:
    # Prova con possibili ticker alternativi
    alt_tickers = ['POLHC', 'POLHC.L', 'POLHC.IR']
    for tick in alt_tickers:
        try:
            stock = yf.Ticker(tick)
            hist = stock.history(period='1y')
            if not hist.empty:
                print(f"   ✓ Trovato con {tick}!")
                print(f"   Date: {hist.index[0].strftime('%d/%m/%Y')} - {hist.index[-1].strftime('%d/%m/%Y')}")
                found = True
                break
        except:
            continue
except:
    pass

if not found:
    print("   X Nessun ticker alternativo trovato")
print()

print("=" * 70)
if found:
    print("CONCLUSIONE: Dati trovati! Aggiorna il config.py con il ticker corretto.")
else:
    print("CONCLUSIONE: Dati non disponibili su Yahoo Finance.")
    print("Possibili cause:")
    print("  - Fondo non quotato/tracciato su Yahoo Finance")
    print("  - Fondo troppo recente o con liquidità limitata")
    print("  - Serve una fonte dati alternativa (Morningstar, Bloomberg, etc.)")
print("=" * 70)
