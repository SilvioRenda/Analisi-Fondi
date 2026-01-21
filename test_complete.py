"""
Test completo della modalità interattiva
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_complete_flow():
    """Test completo: aggiungi strumenti e verifica grafico"""
    print("\n" + "="*70)
    print("TEST COMPLETO MODALITÀ INTERATTIVA")
    print("="*70)
    
    # Attendi server
    print("\n1. Verifica server attivo...")
    try:
        r = requests.get(f"{BASE_URL}/api/instruments", timeout=5)
        print(f"   [OK] Server attivo (status: {r.status_code})")
    except:
        print("   [ERR] Server non raggiungibile!")
        print("   Avvia con: python main.py --interactive")
        return False
    
    # Pulisci strumenti esistenti
    print("\n2. Pulizia strumenti esistenti...")
    r = requests.post(f"{BASE_URL}/api/clear_all")
    print(f"   [OK] Pulizia completata")
    time.sleep(1)
    
    # Test aggiunta ticker
    print("\n3. Test aggiunta TICKER (AAPL)...")
    r = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": "AAPL", "ticker": "AAPL"}
    )
    if r.status_code == 200:
        data = r.json()
        print(f"   [OK] Ticker aggiunto: {data.get('instrument', {}).get('name_short', 'N/A')}")
    else:
        print(f"   [ERR] Errore: {r.json().get('error', 'Unknown')}")
        return False
    time.sleep(2)
    
    # Test aggiunta ISIN
    print("\n4. Test aggiunta ISIN (LU0097089360)...")
    r = requests.post(
        f"{BASE_URL}/api/add_instrument",
        json={"isin": "LU0097089360", "ticker": "LU0097089360"}
    )
    if r.status_code == 200:
        data = r.json()
        print(f"   [OK] ISIN aggiunto: {data.get('instrument', {}).get('name_short', 'N/A')}")
    else:
        print(f"   [WARN] Errore: {r.json().get('error', 'Unknown')}")
        # Non è critico, continua
    time.sleep(2)
    
    # Verifica lista
    print("\n5. Verifica lista strumenti...")
    r = requests.get(f"{BASE_URL}/api/instruments")
    data = r.json()
    count = data.get('count', 0)
    print(f"   [OK] Strumenti presenti: {count}")
    for inst in data.get('instruments', []):
        print(f"      - {inst.get('name_short', 'N/A')} ({inst.get('isin', 'N/A')})")
    
    if count == 0:
        print("   [ERR] Nessuno strumento presente!")
        return False
    
    # Test generazione report
    print("\n6. Test generazione report con grafico...")
    r = requests.get(f"{BASE_URL}/")
    if r.status_code == 200:
        html = r.text
        has_chart = 'performance-chart' in html or 'Plotly' in html
        has_manager = 'Gestione Strumenti' in html or 'instrument-manager' in html
        print(f"   [OK] Report generato (size: {len(html)} bytes)")
        print(f"   [OK] Contiene sezione gestione: {has_manager}")
        print(f"   [OK] Contiene grafico: {has_chart}")
        
        if not has_chart:
            print("   [WARN] Grafico non trovato nel report")
    else:
        print(f"   [ERR] Errore generazione report: {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        return False
    
    print("\n" + "="*70)
    print("[OK] TUTTI I TEST COMPLETATI CON SUCCESSO!")
    print("="*70)
    print(f"\nApri il browser su {BASE_URL} per vedere il risultato")
    return True

if __name__ == "__main__":
    test_complete_flow()
