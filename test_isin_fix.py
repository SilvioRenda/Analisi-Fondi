"""
Script di test per verificare i calcoli ISIN corretti
"""
import sys
from data_collector import DataCollector
from data_processor import DataProcessor
import pandas as pd

def test_isin_calculations():
    """Test calcoli per ISIN specifici"""

    # Crea istanze
    collector = DataCollector()
    processor = DataProcessor()

    # Test 1: Mutual fund USA (dovrebbe usare Adj Close con Dividends=0)
    print("=" * 60)
    print("TEST 1: T. Rowe Price Health Sciences (US87281Y1029)")
    print("=" * 60)
    isin_us = "US87281Y1029"

    print(f"\n1. Downloading dati per {isin_us}...")
    data_us = collector.get_historical_data(isin_us, years=2)

    if data_us is not None and not data_us.empty:
        print(f"   ✓ Dati scaricati: {len(data_us)} giorni")
        print(f"\n2. Verifica struttura dati:")
        print(f"   Colonne: {list(data_us.columns)}")
        print(f"   _is_adjusted: {data_us['_is_adjusted'].iloc[0] if '_is_adjusted' in data_us.columns else 'MISSING!'}")
        print(f"   Dividends totali: {data_us['Dividends'].sum() if 'Dividends' in data_us.columns else 'MISSING!'}")
        print(f"   Capital Gains totali: {data_us['Capital Gains'].sum() if 'Capital Gains' in data_us.columns else 'MISSING!'}")

        # Verifica che per mutual funds USA con Adj Close, Dividends = 0
        is_adjusted = data_us['_is_adjusted'].iloc[0] if '_is_adjusted' in data_us.columns else False
        dividends_sum = data_us['Dividends'].sum() if 'Dividends' in data_us.columns else -1

        if is_adjusted and dividends_sum == 0.0:
            print(f"   ✓ CORRETTO: Adj Close con Dividends=0 (evita doppio conteggio)")
        elif is_adjusted and dividends_sum > 0:
            print(f"   ✗ ERRORE: Adj Close ma Dividends={dividends_sum} (doppio conteggio!)")
        else:
            print(f"   ℹ INFO: Close con Dividends={dividends_sum} (calcolo manuale)")

        # Calcola metriche
        print(f"\n3. Calcolo metriche...")
        normalized = processor.normalize_to_base100(data_us)
        metrics = processor.calculate_metrics(normalized)

        print(f"   Total Return: {metrics['total_return']:.2f}%")
        print(f"   Annualized Return: {metrics['annualized_return']:.2f}%")
        print(f"   Volatility: {metrics['volatility']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    else:
        print(f"   ✗ ERRORE: Nessun dato scaricato per {isin_us}")

    # Test 2: Fondo europeo (dovrebbe usare Close con Dividends separati se presenti)
    print("\n" + "=" * 60)
    print("TEST 2: BlackRock World Healthscience (LU1960219225)")
    print("=" * 60)
    isin_eu = "LU1960219225"

    print(f"\n1. Downloading dati per {isin_eu}...")
    data_eu = collector.get_historical_data(isin_eu, years=2)

    if data_eu is not None and not data_eu.empty:
        print(f"   ✓ Dati scaricati: {len(data_eu)} giorni")
        print(f"\n2. Verifica struttura dati:")
        print(f"   Colonne: {list(data_eu.columns)}")
        print(f"   _is_adjusted: {data_eu['_is_adjusted'].iloc[0] if '_is_adjusted' in data_eu.columns else 'MISSING!'}")
        print(f"   Dividends totali: {data_eu['Dividends'].sum() if 'Dividends' in data_eu.columns else 'MISSING!'}")
        print(f"   Capital Gains totali: {data_eu['Capital Gains'].sum() if 'Capital Gains' in data_eu.columns else 'MISSING!'}")

        # Calcola metriche
        print(f"\n3. Calcolo metriche...")
        normalized = processor.normalize_to_base100(data_eu)
        metrics = processor.calculate_metrics(normalized)

        print(f"   Total Return: {metrics['total_return']:.2f}%")
        print(f"   Annualized Return: {metrics['annualized_return']:.2f}%")
        print(f"   Volatility: {metrics['volatility']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    else:
        print(f"   ✗ ERRORE: Nessun dato scaricato per {isin_eu}")

    print("\n" + "=" * 60)
    print("TEST COMPLETATO")
    print("=" * 60)

if __name__ == "__main__":
    test_isin_calculations()
