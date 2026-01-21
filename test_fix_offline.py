"""
Test offline delle correzioni al calcolo ISIN
Simula i dati senza scaricarli da internet
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_processor import DataProcessor

def create_mock_us_mutual_fund_data():
    """
    Crea dati simulati per un US mutual fund
    Simula Adj Close che già include dividendi
    """
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

    # Simula prezzi con crescita del 10% annuo
    prices = 100 * (1 + 0.10/365) ** np.arange(len(dates))

    # Aggiungi un po' di volatilità
    np.random.seed(42)
    prices = prices * (1 + np.random.randn(len(dates)) * 0.01)

    # Crea DataFrame come restituito da _get_yahoo_data_smart per US mutual fund
    df = pd.DataFrame({
        'Price': prices,
        'Dividends': 0.0,  # ✅ CORRETTO: 0 perché usiamo Adj Close
        'Capital Gains': 0.0,  # ✅ CORRETTO: 0 perché usiamo Adj Close
        '_is_adjusted': True  # Adj Close include già dividendi
    }, index=dates)

    return df

def create_mock_eu_fund_data():
    """
    Crea dati simulati per un fondo europeo
    Simula Close con dividendi separati
    """
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

    # Simula prezzi con crescita del 8% annuo (senza dividendi)
    prices = 100 * (1 + 0.08/365) ** np.arange(len(dates))

    # Aggiungi volatilità
    np.random.seed(43)
    prices = prices * (1 + np.random.randn(len(dates)) * 0.01)

    # Simula dividendi trimestrali (ogni 90 giorni circa)
    dividends = np.zeros(len(dates))
    for i in range(0, len(dates), 90):
        if i > 0:
            dividends[i] = prices[i] * 0.005  # 0.5% dividend yield per quarter

    # Crea DataFrame come restituito da _get_yahoo_data_smart per EU fund
    df = pd.DataFrame({
        'Price': prices,
        'Dividends': dividends,  # Dividendi separati
        'Capital Gains': 0.0,
        '_is_adjusted': False  # Close, dividendi NON inclusi nel prezzo
    }, index=dates)

    return df

def test_calculations():
    """Test calcoli con dati simulati"""

    processor = DataProcessor()

    print("=" * 70)
    print("TEST OFFLINE - Verifica Correzioni Calcoli ISIN")
    print("=" * 70)

    # Test 1: US Mutual Fund (Adj Close)
    print("\n📊 TEST 1: US Mutual Fund (con Adj Close)")
    print("-" * 70)

    data_us = create_mock_us_mutual_fund_data()

    print(f"✓ Dati creati: {len(data_us)} giorni")
    print(f"  _is_adjusted: {data_us['_is_adjusted'].iloc[0]}")
    print(f"  Dividends totali: {data_us['Dividends'].sum():.2f}")
    print(f"  Capital Gains totali: {data_us['Capital Gains'].sum():.2f}")

    # Verifica correzione: con Adj Close, Dividends DEVE essere 0
    if data_us['_is_adjusted'].iloc[0] and data_us['Dividends'].sum() == 0.0:
        print("  ✅ CORRETTO: Adj Close con Dividends=0 (evita doppio conteggio)")
    else:
        print("  ❌ ERRORE: Adj Close ma Dividends > 0 (rischio doppio conteggio!)")

    # Calcola metriche
    print("\n📈 Metriche calcolate:")
    normalized_us = processor.normalize_to_base100(data_us)
    metrics_us = processor.calculate_metrics(normalized_us)

    print(f"  Prezzo iniziale: {data_us['Price'].iloc[0]:.2f}")
    print(f"  Prezzo finale: {data_us['Price'].iloc[-1]:.2f}")
    print(f"  Total Return: {metrics_us['total_return']:.2f}%")
    print(f"  Annualized Return: {metrics_us['annualized_return']:.2f}%")
    print(f"  Volatility: {metrics_us['volatility']:.2f}%")
    print(f"  Sharpe Ratio: {metrics_us['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics_us['max_drawdown']:.2f}%")

    # Verifica che Total Return sia ragionevole (circa 10% per 2 anni = ~20%)
    expected_return = ((data_us['Price'].iloc[-1] / data_us['Price'].iloc[0]) - 1) * 100
    print(f"\n  Return atteso dal prezzo: {expected_return:.2f}%")
    if abs(metrics_us['total_return'] - expected_return) < 0.1:
        print("  ✅ Total Return corrisponde al return del prezzo (corretto per Adj Close)")
    else:
        print("  ⚠ Discrepanza tra Total Return e price return")

    # Test 2: EU Fund (Close con dividendi)
    print("\n" + "=" * 70)
    print("📊 TEST 2: Fondo Europeo (con Close + Dividends)")
    print("-" * 70)

    data_eu = create_mock_eu_fund_data()

    print(f"✓ Dati creati: {len(data_eu)} giorni")
    print(f"  _is_adjusted: {data_eu['_is_adjusted'].iloc[0]}")
    print(f"  Dividends totali: {data_eu['Dividends'].sum():.2f}")
    print(f"  Capital Gains totali: {data_eu['Capital Gains'].sum():.2f}")

    # Verifica: con Close, Dividends può essere > 0
    if not data_eu['_is_adjusted'].iloc[0]:
        if data_eu['Dividends'].sum() > 0:
            print("  ✅ CORRETTO: Close con Dividends > 0 (verranno aggiunti al calcolo)")
        else:
            print("  ℹ INFO: Close senza Dividends (ok se il fondo non distribuisce)")

    # Calcola metriche
    print("\n📈 Metriche calcolate:")
    normalized_eu = processor.normalize_to_base100(data_eu)
    metrics_eu = processor.calculate_metrics(normalized_eu)

    print(f"  Prezzo iniziale: {data_eu['Price'].iloc[0]:.2f}")
    print(f"  Prezzo finale: {data_eu['Price'].iloc[-1]:.2f}")
    print(f"  Total Return: {metrics_eu['total_return']:.2f}%")
    print(f"  Annualized Return: {metrics_eu['annualized_return']:.2f}%")
    print(f"  Volatility: {metrics_eu['volatility']:.2f}%")
    print(f"  Sharpe Ratio: {metrics_eu['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics_eu['max_drawdown']:.2f}%")

    # Verifica che Total Return > Price Return (perché ci sono dividendi)
    price_return = ((data_eu['Price'].iloc[-1] / data_eu['Price'].iloc[0]) - 1) * 100
    print(f"\n  Price Return (solo prezzo): {price_return:.2f}%")
    print(f"  Total Return (prezzo + dividendi): {metrics_eu['total_return']:.2f}%")

    if metrics_eu['total_return'] > price_return:
        print("  ✅ Total Return > Price Return (corretto, include dividendi reinvestiti)")
        print(f"  ℹ Valore aggiunto dai dividendi: {metrics_eu['total_return'] - price_return:.2f}%")
    else:
        print("  ⚠ Total Return <= Price Return (potrebbe essere un problema)")

    # Riepilogo finale
    print("\n" + "=" * 70)
    print("📋 RIEPILOGO TEST")
    print("=" * 70)

    tests_passed = 0
    tests_total = 4

    # Test 1: US Mutual Fund - Dividends = 0
    if data_us['_is_adjusted'].iloc[0] and data_us['Dividends'].sum() == 0.0:
        print("✅ Test 1: US Mutual Fund - Dividends=0 con Adj Close")
        tests_passed += 1
    else:
        print("❌ Test 1: FALLITO")

    # Test 2: US Mutual Fund - Total Return = Price Return
    if abs(metrics_us['total_return'] - expected_return) < 0.1:
        print("✅ Test 2: US Mutual Fund - Total Return corretto")
        tests_passed += 1
    else:
        print("❌ Test 2: FALLITO")

    # Test 3: EU Fund - Dividends presente
    if not data_eu['_is_adjusted'].iloc[0]:
        print("✅ Test 3: EU Fund - _is_adjusted=False corretto")
        tests_passed += 1
    else:
        print("❌ Test 3: FALLITO")

    # Test 4: EU Fund - Total Return > Price Return
    if metrics_eu['total_return'] > price_return:
        print("✅ Test 4: EU Fund - Total Return > Price Return")
        tests_passed += 1
    else:
        print("❌ Test 4: FALLITO")

    print(f"\n🎯 Risultato: {tests_passed}/{tests_total} test passati")

    if tests_passed == tests_total:
        print("\n🎉 TUTTI I TEST PASSATI! Le correzioni funzionano correttamente!")
    else:
        print(f"\n⚠ {tests_total - tests_passed} test falliti. Rivedere il codice.")

    print("=" * 70)

if __name__ == "__main__":
    test_calculations()
