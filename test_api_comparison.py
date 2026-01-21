"""Test comparativo tra diverse API per identificare fonte più affidabile"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from data_collector import DataCollector
from data_processor import DataProcessor
import config

print("=" * 80)
print("TEST COMPARATIVO API - TROVARE FONTE PIU' AFFIDABILE")
print("=" * 80)
print()

# Test con T. Rowe Price (problema noto)
test_isin = 'US87281Y1029'
test_ticker = 'PRHSX'

collector = DataCollector()
processor = DataProcessor()

results = {}

print(f"Test con: {test_isin} (T. Rowe Price Health Sciences)")
print("-" * 80)
print()

# Test 1: Yahoo Finance
print("1. YAHOO FINANCE")
print("-" * 80)
try:
    ticker = yf.Ticker(test_ticker)
    hist_yf = ticker.history(start='2024-01-01', end='2026-01-16')
    if not hist_yf.empty:
        hist_yf = hist_yf[['Close', 'Dividends', 'Capital Gains']].rename(columns={'Close': 'Price'})
        
        # Calcola return 2024
        hist_2024 = hist_yf[hist_yf.index >= '2024-01-01']
        hist_2024 = hist_2024[hist_2024.index < '2025-01-01']
        if not hist_2024.empty:
            normalized_2024 = processor.normalize_to_base100(hist_2024, use_total_return=True)
            return_2024 = ((normalized_2024['Normalized_Value'].iloc[-1] / normalized_2024['Normalized_Value'].iloc[0]) - 1) * 100
        
        # Calcola return 2025
        hist_2025 = hist_yf[hist_yf.index >= '2025-01-01']
        hist_2025 = hist_2025[hist_2025.index < '2026-01-01']
        if not hist_2025.empty:
            normalized_2025 = processor.normalize_to_base100(hist_2025, use_total_return=True)
            return_2025 = ((normalized_2025['Normalized_Value'].iloc[-1] / normalized_2025['Normalized_Value'].iloc[0]) - 1) * 100
        
        results['Yahoo Finance'] = {
            '2024': return_2024 if 'return_2024' in locals() else None,
            '2025': return_2025 if 'return_2025' in locals() else None,
            'available': True
        }
        print(f"[OK] Dati disponibili")
        if 'return_2024' in locals():
            print(f"  Return 2024: {return_2024:.2f}%")
        if 'return_2025' in locals():
            print(f"  Return 2025: {return_2025:.2f}%")
    else:
        results['Yahoo Finance'] = {'available': False}
        print("[ERR] Nessun dato disponibile")
except Exception as e:
    results['Yahoo Finance'] = {'available': False, 'error': str(e)}
    print(f"[ERR] Errore: {e}")
print()

# Test 2: EOD Historical Data
print("2. EOD HISTORICAL DATA")
print("-" * 80)
if config.EOD_API_KEY:
    try:
        data_eod = collector._get_eod_total_return(test_isin, 
                                                   datetime(2024, 1, 1), 
                                                   datetime(2026, 1, 16))
        if data_eod is not None and not data_eod.empty:
            # Calcola return 2024
            data_2024 = data_eod[data_eod.index >= '2024-01-01']
            data_2024 = data_2024[data_2024.index < '2025-01-01']
            if not data_2024.empty:
                normalized_2024 = processor.normalize_to_base100(data_2024, use_total_return=False)
                return_2024 = ((normalized_2024['Normalized_Value'].iloc[-1] / normalized_2024['Normalized_Value'].iloc[0]) - 1) * 100
            
            # Calcola return 2025
            data_2025 = data_eod[data_eod.index >= '2025-01-01']
            data_2025 = data_2025[data_2025.index < '2026-01-01']
            if not data_2025.empty:
                normalized_2025 = processor.normalize_to_base100(data_2025, use_total_return=False)
                return_2025 = ((normalized_2025['Normalized_Value'].iloc[-1] / normalized_2025['Normalized_Value'].iloc[0]) - 1) * 100
            
            results['EOD Historical Data'] = {
                '2024': return_2024 if 'return_2024' in locals() else None,
                '2025': return_2025 if 'return_2025' in locals() else None,
                'available': True
            }
            print(f"[OK] Dati disponibili")
            if 'return_2024' in locals():
                print(f"  Return 2024: {return_2024:.2f}%")
            if 'return_2025' in locals():
                print(f"  Return 2025: {return_2025:.2f}%")
        else:
            results['EOD Historical Data'] = {'available': False}
            print("[ERR] Nessun dato disponibile")
    except Exception as e:
        results['EOD Historical Data'] = {'available': False, 'error': str(e)}
        print(f"[ERR] Errore: {e}")
else:
    results['EOD Historical Data'] = {'available': False, 'reason': 'No API key'}
    print("[SKIP] API key non configurata")
print()

# Test 3: Alpha Vantage
print("3. ALPHA VANTAGE")
print("-" * 80)
if config.ALPHA_VANTAGE_API_KEY and test_ticker:
    try:
        data_av = collector._get_alpha_vantage_adjusted(test_ticker,
                                                         datetime(2024, 1, 1),
                                                         datetime(2026, 1, 16))
        if data_av is not None and not data_av.empty:
            # Calcola return 2024
            data_2024 = data_av[data_av.index >= '2024-01-01']
            data_2024 = data_2024[data_2024.index < '2025-01-01']
            if not data_2024.empty:
                normalized_2024 = processor.normalize_to_base100(data_2024, use_total_return=False)
                return_2024 = ((normalized_2024['Normalized_Value'].iloc[-1] / normalized_2024['Normalized_Value'].iloc[0]) - 1) * 100
            
            # Calcola return 2025
            data_2025 = data_av[data_av.index >= '2025-01-01']
            data_2025 = data_2025[data_2025.index < '2026-01-01']
            if not data_2025.empty:
                normalized_2025 = processor.normalize_to_base100(data_2025, use_total_return=False)
                return_2025 = ((normalized_2025['Normalized_Value'].iloc[-1] / normalized_2025['Normalized_Value'].iloc[0]) - 1) * 100
            
            results['Alpha Vantage'] = {
                '2024': return_2024 if 'return_2024' in locals() else None,
                '2025': return_2025 if 'return_2025' in locals() else None,
                'available': True
            }
            print(f"[OK] Dati disponibili")
            if 'return_2024' in locals():
                print(f"  Return 2024: {return_2024:.2f}%")
            if 'return_2025' in locals():
                print(f"  Return 2025: {return_2025:.2f}%")
        else:
            results['Alpha Vantage'] = {'available': False}
            print("[ERR] Nessun dato disponibile")
    except Exception as e:
        results['Alpha Vantage'] = {'available': False, 'error': str(e)}
        print(f"[ERR] Errore: {e}")
else:
    if not config.ALPHA_VANTAGE_API_KEY:
        results['Alpha Vantage'] = {'available': False, 'reason': 'No API key'}
        print("[SKIP] API key non configurata")
    else:
        results['Alpha Vantage'] = {'available': False, 'reason': 'No ticker'}
        print("[SKIP] Ticker non disponibile")
print()

# Test 4: Financial Modeling Prep
print("4. FINANCIAL MODELING PREP")
print("-" * 80)
if config.FMP_API_KEY:
    try:
        data_fmp = collector._get_fmp_historical(test_isin,
                                                   datetime(2024, 1, 1),
                                                   datetime(2026, 1, 16))
        if data_fmp is not None and not data_fmp.empty:
            # Calcola return 2024
            data_2024 = data_fmp[data_fmp.index >= '2024-01-01']
            data_2024 = data_2024[data_2024.index < '2025-01-01']
            if not data_2024.empty:
                normalized_2024 = processor.normalize_to_base100(data_2024, use_total_return=False)
                return_2024 = ((normalized_2024['Normalized_Value'].iloc[-1] / normalized_2024['Normalized_Value'].iloc[0]) - 1) * 100
            
            # Calcola return 2025
            data_2025 = data_fmp[data_fmp.index >= '2025-01-01']
            data_2025 = data_2025[data_2025.index < '2026-01-01']
            if not data_2025.empty:
                normalized_2025 = processor.normalize_to_base100(data_2025, use_total_return=False)
                return_2025 = ((normalized_2025['Normalized_Value'].iloc[-1] / normalized_2025['Normalized_Value'].iloc[0]) - 1) * 100
            
            results['Financial Modeling Prep'] = {
                '2024': return_2024 if 'return_2024' in locals() else None,
                '2025': return_2025 if 'return_2025' in locals() else None,
                'available': True
            }
            print(f"[OK] Dati disponibili")
            if 'return_2024' in locals():
                print(f"  Return 2024: {return_2024:.2f}%")
            if 'return_2025' in locals():
                print(f"  Return 2025: {return_2025:.2f}%")
        else:
            results['Financial Modeling Prep'] = {'available': False}
            print("[ERR] Nessun dato disponibile")
    except Exception as e:
        results['Financial Modeling Prep'] = {'available': False, 'error': str(e)}
        print(f"[ERR] Errore: {e}")
else:
    results['Financial Modeling Prep'] = {'available': False, 'reason': 'No API key'}
    print("[SKIP] API key non configurata")
print()

# Confronto con dati ufficiali (se disponibili)
print("=" * 80)
print("CONFRONTO RISULTATI")
print("=" * 80)
print()

# Dati ufficiali banca (per riferimento)
official_2024 = 1.94
official_2025 = 17.89

print(f"Dati ufficiali banca:")
print(f"  2024: {official_2024:.2f}%")
print(f"  2025: {official_2025:.2f}%")
print()

print("Risultati API:")
for api_name, api_results in results.items():
    if api_results.get('available'):
        print(f"\n{api_name}:")
        if '2024' in api_results and api_results['2024'] is not None:
            diff_2024 = abs(api_results['2024'] - official_2024)
            print(f"  2024: {api_results['2024']:.2f}% (diff: {diff_2024:.2f}%)")
        if '2025' in api_results and api_results['2025'] is not None:
            diff_2025 = abs(api_results['2025'] - official_2025)
            print(f"  2025: {api_results['2025']:.2f}% (diff: {diff_2025:.2f}%)")
    else:
        reason = api_results.get('reason', api_results.get('error', 'Unknown'))
        print(f"\n{api_name}: [NON DISPONIBILE] - {reason}")

print()
print("=" * 80)
print("TEST COMPLETATO")
print("=" * 80)
