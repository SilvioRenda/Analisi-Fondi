"""
Entry point principale per l'analisi comparativa dei fondi healthcare
"""

import os
import argparse
import webbrowser
from datetime import datetime
import config
from data_collector import DataCollector
from data_processor import DataProcessor
from visualizer import Visualizer
from fund_manager import FundManager


def main():
    """
    Funzione principale che orchestra tutto il processo di analisi
    """
    parser = argparse.ArgumentParser(
        description='Analisi Comparativa Fondi Healthcare',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python main.py                          # Usa fondi da config.py
  python main.py --isin LU0097089360     # Analizza singolo ISIN
  python main.py --isin-list funds.txt   # Analizza ISIN da file
  python main.py --funds-file funds.json # Usa configurazione JSON custom
        """
    )
    parser.add_argument('--isin', type=str, help='Analizza singolo ISIN')
    parser.add_argument('--isin-list', type=str, help='File con lista ISIN (uno per riga)')
    parser.add_argument('--funds-file', type=str, help='File JSON con configurazione fondi')
    parser.add_argument('--use-config', action='store_true', help='Usa fondi da config.py (default)')
    parser.add_argument('--interactive', action='store_true', help='Avvia server interattivo (report parte vuoto)')
    parser.add_argument('--port', type=int, default=5000, help='Porta server interattivo (default: 5000)')
    
    args = parser.parse_args()
    
    # Se modalità interattiva, avvia server e esci
    if args.interactive:
        from web_server import run_server
        run_server(port=args.port, open_browser=True)
        return
    
    print("=" * 60)
    print("ANALISI COMPARATIVA FONDI HEALTHCARE")
    print("=" * 60)
    print()
    
    # Crea directory di output se non esiste
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Inizializza componenti
    print("Inizializzazione componenti...")
    collector = DataCollector()
    processor = DataProcessor()
    visualizer = Visualizer()
    fund_manager = FundManager()
    
    # Fase 1: Raccolta dati - Gestione input flessibile
    print("\n" + "=" * 60)
    print("FASE 1: Raccolta dati storici e composizione fondi")
    print("=" * 60)
    
    funds_data = {}
    funds_config = None
    
    if args.isin:
        # Analizza singolo ISIN
        print(f"Analisi singolo ISIN: {args.isin}")
        fund_data = collector.analyze_single_fund(args.isin, config.YEARS_BACK)
        # Converti in formato compatibile con process_all_funds
        funds_data[fund_data['name']] = {
            'isin': fund_data['isin'],
            'name_short': fund_data['name_short'],
            'historical_data': fund_data['historical_data'],
            'composition': fund_data['composition']
        }
    elif args.isin_list:
        # Carica ISIN da file di testo
        print(f"Caricamento ISIN da file: {args.isin_list}")
        funds_config = fund_manager.load_funds_from_file(args.isin_list, auto_fetch_metadata=True)
        funds_data = collector.collect_all_funds_data(funds_config)
    elif args.funds_file:
        # Carica configurazione da file JSON
        print(f"Caricamento configurazione da: {args.funds_file}")
        funds_config = fund_manager.load_funds_from_file(args.funds_file, auto_fetch_metadata=False)
        funds_data = collector.collect_all_funds_data(funds_config)
    else:
        # Usa configurazione default da config.py
        print("Uso configurazione da config.py")
        funds_data = collector.collect_all_funds_data()
    
    # Verifica quanti fondi hanno dati
    funds_with_data = sum(1 for f in funds_data.values() 
                         if f.get('historical_data') is not None 
                         and not f['historical_data'].empty)
    print(f"\nFondi con dati storici disponibili: {funds_with_data}/{len(funds_data)}")
    
    # Fase 2: Elaborazione dati
    print("\n" + "=" * 60)
    print("FASE 2: Elaborazione e normalizzazione dati")
    print("=" * 60)
    processed_data = processor.process_all_funds(funds_data, collector=collector)
    
    # Crea DataFrame comparativo
    comparison_df = processor.create_comparison_dataframe(processed_data)
    
    if comparison_df.empty:
        print("\nATTENZIONE: Nessun dato disponibile per la visualizzazione.")
        print("   Verifica la connessione internet e la disponibilità dei dati sui fondi.")
        return
    
    print(f"\nSerie temporali elaborate: {len(comparison_df.columns)}")
    print(f"Periodo analizzato: {comparison_df.index[0].strftime('%d/%m/%Y')} - {comparison_df.index[-1].strftime('%d/%m/%Y')}")
    
    # Fase 3: Generazione report
    print("\n" + "=" * 60)
    print("FASE 3: Generazione report HTML")
    print("=" * 60)
    
    template_path = os.path.join(config.TEMPLATES_DIR, 'report.html')
    if not os.path.exists(template_path):
        print(f"ERRORE: Template non trovato in {template_path}")
        return
    
    report_html = visualizer.generate_full_report(
        comparison_df, 
        processed_data, 
        template_path
    )
    
    # Aggiungi data di generazione
    generation_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    report_html = report_html.replace('{{GENERATION_DATE}}', generation_date)
    
    # Salva report
    output_path = os.path.join(config.OUTPUT_DIR, 'report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    
    print(f"\nReport generato con successo!")
    print(f"   Percorso: {os.path.abspath(output_path)}")
    # Apri automaticamente il report nel browser
    try:
        file_url = f"file:///{os.path.abspath(output_path).replace(os.sep, '/')}"
        webbrowser.open(file_url)
        print(f"\n   Report aperto automaticamente nel browser.")
    except Exception as e:
        print(f"\n   Impossibile aprire automaticamente il browser: {e}")
        print(f"   Apri manualmente il file: {os.path.abspath(output_path)}")
    
    # Riepilogo metriche
    print("\n" + "=" * 60)
    print("RIEPILOGO METRICHE")
    print("=" * 60)
    for fund_name, fund_data in processed_data.items():
        metrics = fund_data.get('metrics', {})
        name_short = fund_data.get('name_short', fund_name)
        
        if metrics.get('total_return') is not None:
            print(f"\n{name_short}:")
            print(f"  Return Totale: {metrics.get('total_return', 'N/A')}%")
            print(f"  Return Annualizzato: {metrics.get('annualized_return', 'N/A')}%")
            print(f"  Volatilità: {metrics.get('volatility', 'N/A')}%")
        else:
            print(f"\n{name_short}: Dati non disponibili")
    
    print("\n" + "=" * 60)
    print("ANALISI COMPLETATA")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperazione interrotta dall'utente.")
    except Exception as e:
        print(f"\nERRORE durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
    except SystemExit:
        # argparse può chiamare sys.exit(), gestiamolo silenziosamente
        pass