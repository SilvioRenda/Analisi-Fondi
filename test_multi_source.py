"""Test del sistema multi-fonte per recupero dati"""
from data_collector import DataCollector
import pandas as pd

print("=" * 70)
print("TEST SISTEMA MULTI-FONTE")
print("=" * 70)
print()

dc = DataCollector()

# Test 1: Fondo con ticker noto (dovrebbe funzionare)
print("1. Test T. Rowe Price (ticker noto PRHSX):")
print("-" * 70)
data = dc.get_historical_data('US87281Y1029', 2)
if data is not None and not data.empty:
    print(f"   OK - Dati trovati! Record: {len(data)}")
    try:
        if isinstance(data.index, pd.DatetimeIndex):
            print(f"   Date: {data.index[0].strftime('%d/%m/%Y')} - {data.index[-1].strftime('%d/%m/%Y')}")
        else:
            print(f"   Date: {str(data.index[0])} - {str(data.index[-1])}")
    except:
        print(f"   Primi valori: {data.head(3)}")
else:
    print("   X - Dati non trovati")
print()

# Test 2: Nuovo fondo JSS
print("2. Test JSS Future Health (nuovo ISIN LU2041626974):")
print("-" * 70)
data = dc.get_historical_data('LU2041626974', 2)
if data is not None and not data.empty:
    print(f"   OK - Dati trovati! Record: {len(data)}")
    try:
        if isinstance(data.index, pd.DatetimeIndex):
            print(f"   Date: {data.index[0].strftime('%d/%m/%Y')} - {data.index[-1].strftime('%d/%m/%Y')}")
        else:
            print(f"   Date: {str(data.index[0])} - {str(data.index[-1])}")
    except:
        print(f"   Primi valori: {data.head(3)}")
else:
    print("   X - Dati non disponibili (verranno provate tutte le fonti)")
print()

# Test 3: Polar Capital (problema noto)
print("3. Test Polar Capital (ISIN IE00BKSBD728):")
print("-" * 70)
data = dc.get_historical_data('IE00BKSBD728', 2)
if data is not None and not data.empty:
    print(f"   OK - Dati trovati! Record: {len(data)}")
    try:
        if isinstance(data.index, pd.DatetimeIndex):
            print(f"   Date: {data.index[0].strftime('%d/%m/%Y')} - {data.index[-1].strftime('%d/%m/%Y')}")
        else:
            print(f"   Date: {str(data.index[0])} - {str(data.index[-1])}")
    except:
        print(f"   Primi valori: {data.head(3)}")
else:
    print("   X - Dati non disponibili (verranno provate tutte le fonti)")
print()

print("=" * 70)
print("Sistema multi-fonte implementato!")
print("Fonti provate in ordine:")
print("  1. Yahoo Finance (ticker)")
print("  2. Yahoo Finance (ISIN.Exchange)")
print("  3. Yahoo Finance (ISIN diretto)")
print("  4. Yahoo Finance (exchange IR per fondi IE)")
print("  5. Morningstar scraping")
print("  6. Finanzen.net scraping")
print("  7. JustETF scraping")
print("=" * 70)
