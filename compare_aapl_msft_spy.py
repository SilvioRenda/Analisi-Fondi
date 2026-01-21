"""Confronto tra Apple, Microsoft e S&P 500"""
import sys
from data_collector import DataCollector
from data_processor import DataProcessor
from visualizer import Visualizer
from datetime import datetime, timedelta
import os

# Configurazione strumenti da confrontare
INSTRUMENTS_CONFIG = {
    'AAPL': {
        'name': 'Apple Inc.',
        'name_short': 'Apple',
        'ticker': 'AAPL',
        'type': 'stock'
    },
    'MSFT': {
        'name': 'Microsoft Corporation',
        'name_short': 'Microsoft',
        'ticker': 'MSFT',
        'type': 'stock'
    },
    'SPY': {
        'name': 'S&P 500',
        'name_short': 'S&P 500',
        'ticker': 'SPY',
        'type': 'index'
    }
}

def main():
    print("=" * 70)
    print("CONFRONTO: Apple vs Microsoft vs S&P 500")
    print("=" * 70)
    print()
    
    collector = DataCollector()
    processor = DataProcessor()
    visualizer = Visualizer()
    
    # Fase 1: Raccolta dati
    print("=" * 70)
    print("FASE 1: Raccolta dati storici")
    print("=" * 70)
    
    instruments_data = {}
    years_back = 5  # 5 anni di dati
    
    for ticker, config in INSTRUMENTS_CONFIG.items():
        print(f"Raccolta dati per {config['name']} ({ticker})...")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years_back * 365)
            
            # Usa _get_yahoo_data_smart direttamente con il ticker
            data = collector._get_yahoo_data_smart(
                ticker, 
                start_date, 
                end_date, 
                is_us_mutual_fund=False
            )
            
            if data is not None and not data.empty:
                # Recupera descrizione dettagliata
                description, description_source = collector.get_fund_description(
                    ticker,  # isin (usa ticker come ISIN)
                    ticker=ticker,  # ticker
                    name=config['name']  # name
                )
                
                instruments_data[config['name']] = {
                    'isin': ticker,  # Usa ticker come ISIN per compatibilità
                    'ticker': ticker,
                    'name_short': config['name_short'],
                    'historical_data': data,
                    'composition': {},  # Non necessario per titoli/indici
                    'description': description,
                    'description_source': description_source
                }
                print(f"  [OK] Dati recuperati: {len(data)} giorni")
                if description:
                    print(f"  [OK] Descrizione recuperata da: {description_source}")
            else:
                print(f"  [ERR] Nessun dato disponibile")
        except Exception as e:
            print(f"  [ERR] Errore: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nStrumenti con dati disponibili: {len(instruments_data)}/{len(INSTRUMENTS_CONFIG)}")
    
    if len(instruments_data) == 0:
        print("ERRORE: Nessun dato disponibile per il confronto")
        return
    
    # Fase 2: Elaborazione dati
    print("\n" + "=" * 70)
    print("FASE 2: Elaborazione e normalizzazione dati")
    print("=" * 70)
    
    processed_data = processor.process_all_funds(instruments_data, collector=collector)
    
    # Crea DataFrame comparativo
    comparison_df = processor.create_comparison_dataframe(processed_data)
    
    if comparison_df.empty:
        print("ERRORE: Nessun dato disponibile per il confronto")
        return
    
    print(f"DataFrame comparativo creato: {len(comparison_df)} giorni, {len(comparison_df.columns)} strumenti")
    
    # Fase 3: Generazione report
    print("\n" + "=" * 70)
    print("FASE 3: Generazione report")
    print("=" * 70)
    
    # Crea directory output se non esiste
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    template_path = 'templates/report_template.html'
    if not os.path.exists(template_path):
        template_path = 'templates/report.html'
    
    report_path = os.path.join(output_dir, 'aapl_msft_spy_comparison.html')
    html_content = visualizer.generate_full_report(comparison_df, processed_data, template_path)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generato: {report_path}")
    
    # Stampa metriche
    print("\n" + "=" * 70)
    print("METRICHE PERFORMANCE")
    print("=" * 70)
    print()
    
    for instrument_name, instrument_data in processed_data.items():
        metrics = instrument_data.get('metrics', {})
        name_short = instrument_data.get('name_short', instrument_name)
        
        print(f"{name_short}:")
        if metrics:
            print(f"  Return Totale: {metrics.get('total_return', 'N/A')}%")
            print(f"  Return Annualizzato: {metrics.get('annualized_return', 'N/A')}%")
            print(f"  Volatilità: {metrics.get('volatility', 'N/A')}%")
            print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
            print(f"  Max Drawdown: {metrics.get('max_drawdown', 'N/A')}%")
        else:
            print("  Dati non disponibili")
        print()
    
    # Apri il report nel browser
    import webbrowser
    file_url = f"file:///{os.path.abspath(report_path).replace(os.sep, '/')}"
    webbrowser.open(file_url)
    print(f"Report aperto nel browser")
    
    print("\n" + "=" * 70)
    print("ANALISI COMPLETATA")
    print("=" * 70)

if __name__ == '__main__':
    main()
