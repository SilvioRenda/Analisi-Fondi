"""
Utility per aggiungere fondi dinamicamente e testare recupero dati
"""

import sys
import os
from fund_manager import FundManager
from data_collector import DataCollector
import config


def main():
    """Aggiunge fondi per ISIN e testa recupero dati"""
    if len(sys.argv) < 2:
        print("=" * 70)
        print("UTILITY AGGIUNTA FONDI")
        print("=" * 70)
        print()
        print("Usage: python add_fund.py <ISIN> [ISIN2] [ISIN3] ...")
        print()
        print("Esempi:")
        print("  python add_fund.py LU0097089360")
        print("  python add_fund.py LU0097089360 LU1960219225 LU0823417067")
        print()
        print("L'utility:")
        print("  1. Recupera metadati del fondo tramite Open FIGI")
        print("  2. Testa il recupero dati storici")
        print("  3. Mostra informazioni sul fondo")
        print("=" * 70)
        sys.exit(1)
    
    isins = sys.argv[1:]
    manager = FundManager()
    collector = DataCollector()
    
    print("=" * 70)
    print("AGGIUNTA E TEST FONDI")
    print("=" * 70)
    print()
    
    results = []
    
    for isin in isins:
        isin = isin.strip().upper()
        if len(isin) < 12:
            print(f"[WARN] ISIN non valido (troppo corto): {isin}")
            continue
        
        print(f"\n{'='*70}")
        print(f"Fondo: {isin}")
        print(f"{'='*70}")
        
        # 1. Recupera metadati
        print("1. Recupero metadati da Open FIGI...")
        fund_info = manager.add_fund_by_isin(isin, auto_fetch_metadata=True)
        
        if fund_info.get('name_short') and fund_info['name_short'] != f'Fondo {isin}':
            print(f"   [OK] Nome: {fund_info['name_short']}")
        else:
            print(f"   [WARN] Nome non trovato, usando: {fund_info['name_short']}")
        
        if fund_info.get('ticker'):
            print(f"   [OK] Ticker: {fund_info['ticker']}")
        if fund_info.get('exchange'):
            print(f"   [OK] Exchange: {fund_info['exchange']}")
        if fund_info.get('category'):
            print(f"   [OK] Categoria: {fund_info['category']}")
        
        # 2. Test recupero dati storici
        print("\n2. Test recupero dati storici...")
        try:
            data = collector.get_historical_data(isin, years=1)
            if data is not None and not data.empty:
                print(f"   [OK] Dati disponibili: {len(data)} record")
                if isinstance(data.index, type(data.index)) and hasattr(data.index[0], 'strftime'):
                    print(f"   [OK] Periodo: {data.index[0].strftime('%d/%m/%Y')} - {data.index[-1].strftime('%d/%m/%Y')}")
                print(f"   [OK] Ultimo prezzo: {data['Price'].iloc[-1]:.4f}")
            else:
                print(f"   [WARN] Dati non disponibili")
        except Exception as e:
            print(f"   [ERR] Errore: {e}")
        
        # 3. Test composizione
        print("\n3. Test recupero composizione...")
        try:
            composition = collector.get_fund_composition(isin)
            if composition.get('sectors') or composition.get('top_holdings'):
                print(f"   [OK] Composizione disponibile")
                if composition.get('data_source'):
                    print(f"   [OK] Fonte: {composition['data_source']}")
            else:
                print(f"   [WARN] Composizione non disponibile")
        except Exception as e:
            print(f"   [ERR] Errore: {e}")
        
        results.append({
            'isin': isin,
            'fund_info': fund_info,
            'has_data': data is not None and not data.empty if 'data' in locals() else False
        })
    
    # Riepilogo
    print(f"\n{'='*70}")
    print("RIEPILOGO")
    print(f"{'='*70}")
    print(f"Fondi processati: {len(results)}")
    print(f"Fondi con dati: {sum(1 for r in results if r['has_data'])}")
    
    # Suggerimento per salvare
    if len(results) > 0:
        print(f"\nPer salvare questi fondi in un file:")
        print(f"  1. Crea un file funds_list.txt con gli ISIN (uno per riga)")
        print(f"  2. Oppure usa: python main.py --isin-list funds_list.txt")
        print(f"\nISIN da aggiungere a funds_list.txt:")
        for r in results:
            print(f"  {r['isin']}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperazione interrotta dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERRORE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
