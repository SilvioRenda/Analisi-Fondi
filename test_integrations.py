"""
Test per integrazioni librerie GitHub
"""

import sys
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_lib_manager():
    """Test LibraryManager"""
    print("=" * 60)
    print("TEST: LibraryManager")
    print("=" * 60)
    
    try:
        from lib_manager import LibraryManager
        manager = LibraryManager()
        
        status = manager.get_status()
        print("\nStato librerie:")
        for lib, available in status.items():
            status_str = "OK - Disponibile" if available else "NO - Non disponibile"
            print(f"  {lib}: {status_str}")
        
        print("\nOK - LibraryManager test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore LibraryManager: {e}")
        return False

def test_sector_classifier():
    """Test SectorClassifier"""
    print("\n" + "=" * 60)
    print("TEST: SectorClassifier")
    print("=" * 60)
    
    try:
        from sector_classifier import SectorClassifier
        classifier = SectorClassifier()
        
        # Test classificazione
        test_fund = {
            'name_short': 'Apple Inc.',
            'isin': 'US0378331005',
            'ticker': 'AAPL'
        }
        
        sector = classifier.classify_fund(test_fund, ticker='AAPL', isin='US0378331005')
        print(f"\nSettore classificato per Apple: {sector}")
        
        print("\nOK - SectorClassifier test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore SectorClassifier: {e}")
        return False

def test_advanced_metrics():
    """Test AdvancedMetricsCalculator"""
    print("\n" + "=" * 60)
    print("TEST: AdvancedMetricsCalculator")
    print("=" * 60)
    
    try:
        from advanced_metrics import AdvancedMetricsCalculator
        calc = AdvancedMetricsCalculator()
        
        # Crea dati test
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        
        # Test calcolo da dati
        metrics = calc.calculate_from_data(returns)
        print(f"\nMetriche calcolate: {list(metrics.keys())}")
        
        print("\nOK - AdvancedMetricsCalculator test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore AdvancedMetricsCalculator: {e}")
        return False

def test_portfolio_analyzer():
    """Test PortfolioAnalyzer"""
    print("\n" + "=" * 60)
    print("TEST: PortfolioAnalyzer")
    print("=" * 60)
    
    try:
        from portfolio_analyzer import PortfolioAnalyzer
        analyzer = PortfolioAnalyzer()
        
        # Crea dati test
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        returns_df = pd.DataFrame({
            'Fund1': np.random.normal(0.001, 0.02, len(dates)),
            'Fund2': np.random.normal(0.001, 0.015, len(dates)),
            'Fund3': np.random.normal(0.001, 0.025, len(dates))
        }, index=dates)
        
        # Test metriche portfolio
        metrics = analyzer.calculate_portfolio_metrics(returns_df)
        print(f"\nMetriche portfolio: {list(metrics.keys())}")
        
        print("\nOK - PortfolioAnalyzer test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore PortfolioAnalyzer: {e}")
        return False

def test_technical_indicators():
    """Test TechnicalIndicators"""
    print("\n" + "=" * 60)
    print("TEST: TechnicalIndicators")
    print("=" * 60)
    
    try:
        from technical_indicators import TechnicalIndicators
        indicators = TechnicalIndicators()
        
        # Crea dati test
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
        price_df = pd.DataFrame({'Price': prices}, index=dates)
        
        # Test calcolo indicatori
        indicators_df = indicators.calculate_indicators(price_df)
        print(f"\nIndicatori calcolati: {[col for col in indicators_df.columns if col != 'Price']}")
        
        # Test segnali
        signals_df = indicators.generate_signals(indicators_df)
        print(f"Segnali generati: {[col for col in signals_df.columns if 'signal' in col.lower()]}")
        
        print("\nOK - TechnicalIndicators test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore TechnicalIndicators: {e}")
        return False

def test_fallback():
    """Test che fallback funzioni quando librerie non disponibili"""
    print("\n" + "=" * 60)
    print("TEST: Fallback quando librerie non disponibili")
    print("=" * 60)
    
    # Test che il sistema continui a funzionare anche senza librerie avanzate
    try:
        from data_processor import DataProcessor
        processor = DataProcessor()
        
        # Dovrebbe funzionare anche senza librerie avanzate
        test_data = {
            'name_short': 'Test Fund',
            'isin': 'TEST123456789',
            'ticker': 'TEST'
        }
        
        sector = processor._determine_sector(test_data)
        print(f"\nSettore determinato (fallback): {sector}")
        
        print("\nOK - Fallback test completato")
        return True
    except Exception as e:
        print(f"\nERR - Errore fallback: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("=" * 60)
    print("TEST INTEGRAZIONI LIBRERIE GITHUB")
    print("=" * 60)
    
    results = []
    
    results.append(("LibraryManager", test_lib_manager()))
    results.append(("SectorClassifier", test_sector_classifier()))
    results.append(("AdvancedMetrics", test_advanced_metrics()))
    results.append(("PortfolioAnalyzer", test_portfolio_analyzer()))
    results.append(("TechnicalIndicators", test_technical_indicators()))
    results.append(("Fallback", test_fallback()))
    
    # Riepilogo
    print("\n" + "=" * 60)
    print("RIEPILOGO TEST")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {name}")
    
    print(f"\nTest passati: {passed}/{total}")
    
    if passed == total:
        print("\nOK - Tutti i test passati!")
        return 0
    else:
        print(f"\nATTENZIONE - {total - passed} test falliti")
        return 1

if __name__ == "__main__":
    sys.exit(main())
