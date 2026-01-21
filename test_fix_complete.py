"""
Test completo di tutti gli scenari dopo i fix
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_scenario(name, test_func):
    """Esegue un test scenario"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    try:
        result = test_func()
        if result:
            print(f"[OK] {name} - PASSATO")
        else:
            print(f"[FAIL] {name} - FALLITO")
        return result
    except Exception as e:
        print(f"[ERROR] {name} - ECCEZIONE: {e}")
        return False

def test_1_empty_report():
    """Test 1: Report vuoto (0 strumenti)"""
    try:
        r = requests.post(f"{BASE_URL}/api/clear_all", timeout=5)
        time.sleep(0.5)
        
        r = requests.get(f"{BASE_URL}/", timeout=10)
        if r.status_code == 200:
            html = r.text
            has_empty = 'Nessun strumento selezionato' in html or 'empty-state' in html or 'Nessun strumento aggiunto' in html
            has_manager = 'Gestione Strumenti' in html or 'instrument-manager' in html or 'isin-input' in html
            print(f"  DEBUG: has_empty={has_empty}, has_manager={has_manager}")
            return has_empty and has_manager
        else:
            print(f"  DEBUG: Status code: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ERROR: Server non raggiungibile. Avvia il server con: python main.py --interactive")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_2_add_ticker():
    """Test 2: Aggiunta ticker (AAPL)"""
    r = requests.post(f"{BASE_URL}/api/clear_all")
    time.sleep(0.5)
    
    r = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": "AAPL", "ticker": "AAPL"}
    )
    if r.status_code == 200:
        data = r.json()
        return data.get('success', False)
    return False

def test_3_add_isin():
    """Test 3: Aggiunta ISIN (LU0097089360)"""
    r = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": "LU0097089360", "ticker": "LU0097089360"}
    )
    # Può fallire se dati non disponibili, ma deve dare errore chiaro
    if r.status_code == 200:
        return True
    elif r.status_code in [404, 500]:
        data = r.json()
        error = data.get('error', '')
        return 'error' in error.lower() or 'non disponibili' in error.lower() or 'dati' in error.lower()
    return False

def test_4_report_one_instrument():
    """Test 4: Report con 1 strumento valido"""
    try:
        r = requests.post(f"{BASE_URL}/api/clear_all", timeout=5)
        time.sleep(0.5)
        
        r = requests.post(
            f"{BASE_URL}/api/add_instrument",
            json={"isin": "AAPL", "ticker": "AAPL"},
            timeout=30
        )
        if r.status_code != 200:
            print(f"  DEBUG: add_instrument status: {r.status_code}, response: {r.text[:200]}")
            return False
        
        time.sleep(3)  # Attendi generazione dati
        
        r = requests.get(f"{BASE_URL}/", timeout=30)
        if r.status_code == 200:
            html = r.text
            has_chart = 'performance-chart' in html or 'Plotly' in html or 'chart-container' in html or 'var data =' in html or 'plotly' in html.lower()
            has_manager = 'Gestione Strumenti' in html or 'instrument-manager' in html
            has_aapl = 'AAPL' in html
            print(f"  DEBUG: has_chart={has_chart}, has_manager={has_manager}, has_aapl={has_aapl}")
            return has_chart and has_manager and has_aapl
        else:
            print(f"  DEBUG: Status code: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ERROR: Server non raggiungibile")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_5_report_multiple_instruments():
    """Test 5: Report con multipli strumenti"""
    try:
        r = requests.post(f"{BASE_URL}/api/clear_all", timeout=5)
        time.sleep(0.5)
        
        # Aggiungi AAPL
        r1 = requests.post(
            f"{BASE_URL}/api/add_instrument",
            json={"isin": "AAPL", "ticker": "AAPL"},
            timeout=30
        )
        if r1.status_code != 200:
            print(f"  DEBUG: add AAPL status: {r1.status_code}")
            return False
        time.sleep(2)
        
        # Aggiungi MSFT
        r2 = requests.post(
            f"{BASE_URL}/api/add_instrument",
            json={"isin": "MSFT", "ticker": "MSFT"},
            timeout=30
        )
        if r2.status_code != 200:
            print(f"  DEBUG: add MSFT status: {r2.status_code}")
            return False
        time.sleep(3)  # Attendi generazione dati
        
        r = requests.get(f"{BASE_URL}/", timeout=30)
        if r.status_code == 200:
            html = r.text
            has_chart = 'performance-chart' in html or 'Plotly' in html or 'var data =' in html
            has_aapl = 'AAPL' in html
            has_msft = 'MSFT' in html
            print(f"  DEBUG: has_chart={has_chart}, has_aapl={has_aapl}, has_msft={has_msft}")
            return has_chart and (has_aapl or has_msft)
        else:
            print(f"  DEBUG: Status code: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ERROR: Server non raggiungibile")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_6_invalid_data_handling():
    """Test 6: Gestione dati invalidi"""
    r = requests.post(f"{BASE_URL}/api/clear_all")
    time.sleep(0.5)
    
    # Prova ad aggiungere un identificatore invalido
    r = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": "INVALID123", "ticker": "INVALID123"}
    )
    # Dovrebbe dare errore 404 o 500 con messaggio chiaro
    if r.status_code in [404, 500]:
        data = r.json()
        error = data.get('error', '')
        return len(error) > 0  # Deve avere un messaggio di errore
    return False

def main():
    """Esegue tutti i test"""
    print("\n" + "="*70)
    print("TEST COMPLETO POST-FIX")
    print("="*70)
    print("\nAssicurati che il server sia avviato: python main.py --interactive")
    print("Attendere 3 secondi...")
    time.sleep(3)
    
    results = {}
    
    # Test 1: Report vuoto
    results['Report Vuoto'] = test_scenario("Report Vuoto (0 strumenti)", test_1_empty_report)
    
    # Test 2: Aggiunta ticker
    results['Aggiunta Ticker'] = test_scenario("Aggiunta Ticker (AAPL)", test_2_add_ticker)
    
    # Test 3: Aggiunta ISIN
    results['Aggiunta ISIN'] = test_scenario("Aggiunta ISIN (LU0097089360)", test_3_add_isin)
    
    # Test 4: Report 1 strumento
    results['Report 1 Strumento'] = test_scenario("Report con 1 Strumento", test_4_report_one_instrument)
    
    # Test 5: Report multipli strumenti
    results['Report Multipli'] = test_scenario("Report con Multipli Strumenti", test_5_report_multiple_instruments)
    
    # Test 6: Gestione dati invalidi
    results['Dati Invalidi'] = test_scenario("Gestione Dati Invalidi", test_6_invalid_data_handling)
    
    # Riepilogo
    print("\n" + "="*70)
    print("RIEPILOGO TEST")
    print("="*70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nRisultato: {passed}/{total} test passati")
    
    if passed == total:
        print("\n[SUCCESS] Tutti i test sono passati!")
    else:
        print(f"\n[WARNING] {total - passed} test falliti")
    
    return passed == total

if __name__ == "__main__":
    main()
