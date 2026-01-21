"""
Script per installazione e verifica librerie richieste
"""

import sys
import subprocess
import importlib
import warnings

def check_python_version():
    """Verifica versione Python (richiede >= 3.8)"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERRORE: Richiesta Python >= 3.8")
        print(f"Versione attuale: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def install_requirements():
    """Installa librerie da requirements.txt"""
    print("\n" + "=" * 60)
    print("INSTALLAZIONE LIBRERIE")
    print("=" * 60)
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
        print("\n✓ Installazione completata")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Errore durante installazione: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ File requirements.txt non trovato")
        return False

def test_import(library_name: str, import_statement: str) -> bool:
    """
    Testa import di una libreria
    
    Args:
        library_name: Nome libreria per messaggi
        import_statement: Statement da eseguire (es. "import pandas")
    
    Returns:
        True se import riuscito, False altrimenti
    """
    try:
        exec(import_statement)
        print(f"  ✓ {library_name}")
        return True
    except ImportError as e:
        print(f"  ✗ {library_name}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ {library_name}: Errore inatteso - {e}")
        return False

def test_all_libraries():
    """Testa import di tutte le librerie"""
    print("\n" + "=" * 60)
    print("VERIFICA LIBRERIE")
    print("=" * 60)
    
    libraries = {
        # Librerie esistenti
        'yfinance': 'import yfinance',
        'pandas': 'import pandas',
        'numpy': 'import numpy',
        'plotly': 'import plotly',
        'beautifulsoup4': 'from bs4 import BeautifulSoup',
        'requests': 'import requests',
        'jinja2': 'import jinja2',
        'openpyxl': 'import openpyxl',
        'wikipedia': 'import wikipedia',
        
        # Nuove librerie
        'financetoolkit': 'import financetoolkit',
        'FinanceDatabase': 'import FinanceDatabase',
        'Riskfolio-Lib': 'import riskfolio',
        'pandas-ta': 'import pandas_ta',
        'polars': 'import polars',
    }
    
    results = {}
    for lib_name, import_stmt in libraries.items():
        results[lib_name] = test_import(lib_name, import_stmt)
    
    return results

def check_api_keys():
    """Verifica se API keys sono necessarie e configurate"""
    print("\n" + "=" * 60)
    print("VERIFICA API KEYS")
    print("=" * 60)
    
    import os
    import config
    
    api_keys_to_check = {
        'FMP_API_KEY': 'Financial Modeling Prep (opzionale)',
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage (opzionale)',
        'EOD_API_KEY': 'EOD Historical Data (opzionale)',
    }
    
    for key_name, description in api_keys_to_check.items():
        key_value = getattr(config, key_name, None) or os.getenv(key_name, '')
        if key_value:
            print(f"  ✓ {description}: Configurata")
        else:
            print(f"  ⚠ {description}: Non configurata (opzionale)")
    
    # FinanceToolkit potrebbe richiedere API key per alcune funzionalità
    print("\n  Nota: FinanceToolkit può funzionare senza API key per funzionalità base")
    print("        Per funzionalità avanzate, potrebbe essere necessaria una API key")

def main():
    """Funzione principale"""
    print("=" * 60)
    print("INSTALLAZIONE E VERIFICA LIBRERIE")
    print("=" * 60)
    
    # Verifica Python
    if not check_python_version():
        sys.exit(1)
    
    # Chiedi conferma per installazione
    print("\nVuoi installare/aggiornare le librerie? (s/n): ", end='')
    response = input().strip().lower()
    
    if response in ['s', 'si', 'y', 'yes']:
        if not install_requirements():
            print("\nATTENZIONE: Alcune librerie potrebbero non essere state installate correttamente")
    else:
        print("\nInstallazione saltata. Verifico solo librerie esistenti...")
    
    # Testa librerie
    results = test_all_libraries()
    
    # Verifica API keys
    check_api_keys()
    
    # Riepilogo
    print("\n" + "=" * 60)
    print("RIEPILOGO")
    print("=" * 60)
    
    required_libs = ['yfinance', 'pandas', 'numpy', 'plotly', 'beautifulsoup4', 'requests']
    optional_libs = ['financetoolkit', 'FinanceDatabase', 'Riskfolio-Lib', 'pandas-ta', 'polars']
    
    print("\nLibrerie Richieste:")
    all_required_ok = True
    for lib in required_libs:
        status = "✓" if results.get(lib, False) else "✗"
        print(f"  {status} {lib}")
        if not results.get(lib, False):
            all_required_ok = False
    
    print("\nLibrerie Opzionali (per funzionalità avanzate):")
    for lib in optional_libs:
        status = "✓" if results.get(lib, False) else "✗"
        print(f"  {status} {lib}")
    
    if not all_required_ok:
        print("\n⚠ ATTENZIONE: Alcune librerie richieste non sono disponibili!")
        print("   Esegui: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("\n✓ Tutte le librerie richieste sono disponibili")
        if any(results.get(lib, False) for lib in optional_libs):
            print("✓ Alcune funzionalità avanzate sono disponibili")
        else:
            print("⚠ Funzionalità avanzate non disponibili (opzionale)")

if __name__ == "__main__":
    main()
