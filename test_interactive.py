"""
Script di test per modalità interattiva
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_add_instrument(identifier):
    """Test aggiunta strumento"""
    print(f"\n{'='*60}")
    print(f"TEST: Aggiunta strumento {identifier}")
    print(f"{'='*60}")
    
    response = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": identifier, "ticker": identifier},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_get_instruments():
    """Test recupero lista strumenti"""
    print(f"\n{'='*60}")
    print("TEST: Recupero lista strumenti")
    print(f"{'='*60}")
    
    response = requests.get(f"{BASE_URL}/api/instruments")
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Numero strumenti: {data.get('count', 0)}")
    print(f"Strumenti: {json.dumps(data.get('instruments', []), indent=2)}")
    
    return response.status_code == 200

def test_regenerate():
    """Test rigenerazione report"""
    print(f"\n{'='*60}")
    print("TEST: Rigenerazione report")
    print(f"{'='*60}")
    
    response = requests.post(f"{BASE_URL}/api/regenerate")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_get_report():
    """Test recupero report HTML"""
    print(f"\n{'='*60}")
    print("TEST: Recupero report HTML")
    print(f"{'='*60}")
    
    response = requests.get(f"{BASE_URL}/")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)} bytes")
    print(f"Contiene 'Gestione Strumenti': {'Gestione Strumenti' in response.text}")
    print(f"Contiene 'performance-chart': {'performance-chart' in response.text}")
    
    return response.status_code == 200

def main():
    """Esegue tutti i test"""
    print("\n" + "="*60)
    print("TEST MODALITÀ INTERATTIVA")
    print("="*60)
    print("\nAttendere che il server si avvii...")
    time.sleep(3)  # Attendi che il server si avvii
    
    # Test 1: Verifica server attivo
    try:
        test_get_instruments()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRORE: Server non raggiungibile!")
        print("Avvia il server con: python main.py --interactive")
        return
    
    # Test 2: Aggiungi strumento (ticker)
    test_add_instrument("AAPL")
    time.sleep(1)
    
    # Test 3: Verifica lista strumenti
    test_get_instruments()
    time.sleep(1)
    
    # Test 4: Aggiungi altro strumento (ISIN)
    test_add_instrument("LU0097089360")
    time.sleep(1)
    
    # Test 5: Verifica lista aggiornata
    test_get_instruments()
    time.sleep(1)
    
    # Test 6: Recupera report (dovrebbe contenere grafico)
    test_get_report()
    
    # Test 7: Rigenera report
    test_regenerate()
    
    print(f"\n{'='*60}")
    print("TEST COMPLETATI")
    print(f"{'='*60}")
    print("\nApri il browser su http://127.0.0.1:5000 per vedere il risultato")

if __name__ == "__main__":
    main()
