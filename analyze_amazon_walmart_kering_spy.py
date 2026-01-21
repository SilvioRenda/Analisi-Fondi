"""
Script per analizzare Amazon, Walmart, Kering e SP500
"""

import sys
import os
from datetime import datetime
import pandas as pd

# Aggiungi il percorso del progetto al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collector import DataCollector
from data_processor import DataProcessor
from visualizer import Visualizer
import config

def main():
    print("=" * 60)
    print("ANALISI: Amazon, Walmart, Kering vs SP500")
    print("=" * 60)
    print()
    
    # Configurazione strumenti
    instruments_config = {
        "Amazon": {
            "isin": "US0231351067",  # AMZN
            "ticker": "AMZN",
            "name_short": "Amazon",
            "category": "Technology - E-commerce"
        },
        "Walmart": {
            "isin": "US9311421039",  # WMT
            "ticker": "WMT",
            "name_short": "Walmart",
            "category": "Consumer - Retail"
        },
        "Kering": {
            "isin": "FR0000121485",  # KER.PA
            "ticker": "KER.PA",
            "name_short": "Kering",
            "category": "Consumer - Luxury"
        },
        "S&P 500": {
            "isin": "US78463V1070",  # SPY
            "ticker": "SPY",
            "name_short": "S&P 500",
            "category": "Index - US Market"
        }
    }
    
    # Inizializza componenti
    print("Inizializzazione componenti...")
    collector = DataCollector()
    processor = DataProcessor()
    visualizer = Visualizer()
    
    # Fase 1: Raccolta dati
    print("\n" + "=" * 60)
    print("FASE 1: Raccolta dati storici")
    print("=" * 60)
    
    instruments_data = {}
    
    for instrument_name, instrument_config in instruments_config.items():
        isin = instrument_config['isin']
        ticker = instrument_config['ticker']
        name_short = instrument_config['name_short']
        
        print(f"Raccolta dati per {name_short} ({ticker})...")
        
        # Recupera dati storici
        data = collector.get_historical_data(
            isin=isin,
            years=config.YEARS_BACK
        )
        
        if data is not None and not data.empty:
            # Recupera descrizione dettagliata
            description, description_source = collector.get_fund_description(
                isin,
                ticker=ticker,
                name=name_short
            )
            
            instruments_data[instrument_name] = {
                'isin': isin,
                'ticker': ticker,
                'name_short': name_short,
                'historical_data': data,
                'composition': {},  # I titoli azionari non hanno composizione
                'description': description,
                'description_source': description_source
            }
            print(f"  OK - Dati recuperati: {len(data)} record")
        else:
            print(f"  ERR - Nessun dato disponibile per {name_short}")
    
    print(f"\nStrumenti con dati disponibili: {len(instruments_data)}/{len(instruments_config)}")
    
    if not instruments_data:
        print("\nERRORE: Nessun dato disponibile per gli strumenti richiesti.")
        return
    
    # Fase 2: Elaborazione dati
    print("\n" + "=" * 60)
    print("FASE 2: Elaborazione e normalizzazione dati")
    print("=" * 60)
    
    processed_data = processor.process_all_funds(instruments_data, collector=collector)
    
    # Crea DataFrame comparativo
    comparison_df = processor.create_comparison_dataframe(processed_data)
    
    if comparison_df.empty:
        print("\nATTENZIONE: Nessun dato disponibile per la visualizzazione.")
        return
    
    print(f"\nSerie temporali elaborate: {len(comparison_df.columns)}")
    print(f"Periodo analizzato: {comparison_df.index[0].strftime('%d/%m/%Y')} - {comparison_df.index[-1].strftime('%d/%m/%Y')}")
    
    # Fase 3: Generazione report
    print("\n" + "=" * 60)
    print("FASE 3: Generazione report HTML")
    print("=" * 60)
    
    template_path = os.path.join('templates', 'report_template.html')
    report_html = visualizer.generate_full_report(
        comparison_df,
        processed_data,
        template_path
    )
    
    # Salva report
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'amazon_walmart_kering_spy_comparison.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    
    print(f"\nReport generato con successo!")
    print(f"   Percorso: {os.path.abspath(output_path)}")
    
    # Apri automaticamente nel browser
    import webbrowser
    file_url = f"file:///{os.path.abspath(output_path).replace(os.sep, '/')}"
    webbrowser.open(file_url)
    print(f"\n   Report aperto automaticamente nel browser.")
    
    # Riepilogo metriche
    print("\n" + "=" * 60)
    print("RIEPILOGO METRICHE")
    print("=" * 60)
    print()
    
    for instrument_name, instrument_data in processed_data.items():
        metrics = instrument_data.get('metrics', {})
        name_short = instrument_data.get('name_short', instrument_name)
        
        print(f"{name_short}:")
        if metrics:
            print(f"  Return Totale: {metrics.get('total_return', 'N/A')}%")
            print(f"  Return Annualizzato: {metrics.get('annualized_return', 'N/A')}%")
            print(f"  Volatilità: {metrics.get('volatility', 'N/A')}%")
            if metrics.get('beta') is not None:
                benchmark = metrics.get('benchmark', '')
                print(f"  Beta: {metrics.get('beta')} (vs {benchmark})")
        else:
            print("  Dati non disponibili")
        print()
    
    print("=" * 60)
    print("ANALISI COMPLETATA")
    print("=" * 60)

if __name__ == "__main__":
    main()
