"""Analisi comparativa paniere titoli azionari"""
import sys
from data_collector import DataCollector
from data_processor import DataProcessor
from visualizer import Visualizer
from datetime import datetime
import os

# Configurazione titoli da analizzare
STOCKS_CONFIG = {
    'AAPL': {
        'name': 'Apple Inc.',
        'name_short': 'Apple',
        'ticker': 'AAPL'
    },
    'MSFT': {
        'name': 'Microsoft Corporation',
        'name_short': 'Microsoft',
        'ticker': 'MSFT'
    },
    'GOOGL': {
        'name': 'Alphabet Inc. (Class A)',
        'name_short': 'Google',
        'ticker': 'GOOGL'
    },
    'META': {
        'name': 'Meta Platforms Inc.',
        'name_short': 'Meta',
        'ticker': 'META'
    },
    'NVDA': {
        'name': 'NVIDIA Corporation',
        'name_short': 'Nvidia',
        'ticker': 'NVDA'
    },
    'PLTR': {
        'name': 'Palantir Technologies Inc.',
        'name_short': 'Palantir',
        'ticker': 'PLTR'
    },
    'APP': {
        'name': 'AppLovin Corporation',
        'name_short': 'AppLovin',
        'ticker': 'APP'
    }
}

def main():
    print("=" * 70)
    print("ANALISI COMPARATIVA PANIERE TITOLI AZIONARI")
    print("=" * 70)
    print()
    
    collector = DataCollector()
    processor = DataProcessor()
    visualizer = Visualizer()
    
    # Fase 1: Raccolta dati
    print("=" * 70)
    print("FASE 1: Raccolta dati storici")
    print("=" * 70)
    
    stocks_data = {}
    years_back = 3  # 3 anni di dati
    
    for ticker, config in STOCKS_CONFIG.items():
        print(f"Raccolta dati per {config['name']} ({ticker})...")
        
        # Per titoli azionari, usiamo direttamente il ticker con Yahoo Finance
        # Non sono mutual funds USA, quindi is_us_mutual_fund = False
        try:
            from datetime import timedelta
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
                
                stocks_data[config['name']] = {
                    'isin': ticker,  # Usa ticker come ISIN per compatibilità
                    'ticker': ticker,
                    'name_short': config['name_short'],
                    'historical_data': data,
                    'composition': {},  # I titoli azionari non hanno composizione come i fondi
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
    
    print(f"\nTitoli con dati disponibili: {len(stocks_data)}/{len(STOCKS_CONFIG)}")
    
    # Fase 2: Elaborazione dati
    print("\n" + "=" * 70)
    print("FASE 2: Elaborazione e normalizzazione dati")
    print("=" * 70)
    
    processed_data = processor.process_all_funds(stocks_data, collector=collector)
    
    # Crea DataFrame comparativo
    comparison_df = processor.create_comparison_dataframe(processed_data)
    
    if comparison_df.empty:
        print("ERRORE: Nessun dato disponibile per il confronto")
        return
    
    print(f"DataFrame comparativo creato: {len(comparison_df)} giorni, {len(comparison_df.columns)} titoli")
    
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
    
    report_path = os.path.join(output_dir, 'stocks_report.html')
    html_content = visualizer.generate_full_report(comparison_df, processed_data, template_path)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generato: {report_path}")
    
    # Stampa metriche
    print("\n" + "=" * 70)
    print("METRICHE PERFORMANCE")
    print("=" * 70)
    print()
    
    for stock_name, stock_data in processed_data.items():
        metrics = stock_data.get('metrics', {})
        name_short = stock_data.get('name_short', stock_name)
        
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
