"""
Server Flask per interfaccia interattiva selezione ISIN
"""

from flask import Flask, render_template_string, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
import threading
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

import config
from data_collector import DataCollector
from data_processor import DataProcessor
from visualizer import Visualizer
try:
    from fund_manager import FundManager
    fund_manager = FundManager()
except ImportError:
    fund_manager = None

# Configura logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permette chiamate da browser

# Stato globale (in produzione usare session/DB)
current_instruments = {}  # {isin: {ticker, name_short, name, ...}}
instruments_lock = threading.Lock()

# Inizializza componenti
collector = DataCollector()
processor = DataProcessor()
visualizer = Visualizer()


def get_template_path():
    """Restituisce percorso template"""
    template_path = os.path.join('templates', 'report_template.html')
    if not os.path.exists(template_path):
        template_path = os.path.join('templates', 'report.html')
    return template_path


def generate_report_html(instruments_data: Dict = None) -> str:
    """
    Genera report HTML con strumenti specificati
    
    Args:
        instruments_data: Dizionario con dati strumenti (None = report vuoto)
    
    Returns:
        HTML del report
    """
    if instruments_data is None or not instruments_data:
        # Report vuoto - mostra solo interfaccia gestione
        return generate_empty_report()
    
    # Processa dati
    try:
        # VALIDAZIONE PRE-PROCESSING
        logger.info(f"generate_report_html(): Processing {len(instruments_data)} instruments")
        print(f"DEBUG generate_report_html: Processing {len(instruments_data)} instruments")
        
        # Valida che ogni strumento abbia historical_data valido
        for name, data in instruments_data.items():
            hist = data.get('historical_data')
            if hist is None:
                print(f"ERROR: {name} non ha historical_data")
                raise ValueError(f"Strumento {name} non ha dati storici")
            if not isinstance(hist, pd.DataFrame):
                print(f"ERROR: {name} historical_data non è DataFrame")
                raise ValueError(f"Strumento {name} ha dati storici invalidi")
            if hist.empty:
                print(f"ERROR: {name} historical_data è vuoto")
                raise ValueError(f"Strumento {name} ha dati storici vuoti")
            if not isinstance(hist.index, pd.DatetimeIndex):
                print(f"WARNING: {name} historical_data non ha DatetimeIndex")
                # Tenta fix automatico
                if 'Date' in hist.columns:
                    hist['Date'] = pd.to_datetime(hist['Date'])
                    hist = hist.set_index('Date')
                    data['historical_data'] = hist  # Aggiorna
                    print(f"DEBUG: ✓ DatetimeIndex fixato per {name}")
                else:
                    raise ValueError(f"Strumento {name} non può essere normalizzato")
        
        # Se tutte le validazioni passano, procedi
        processed_data = processor.process_all_funds(instruments_data, collector=collector)
        logger.info(f"process_all_funds completato, {len(processed_data)} fondi processati")
        print(f"DEBUG: process_all_funds completato, {len(processed_data)} fondi processati")
        
    except ValueError as ve:
        # Errore di validazione - dati invalidi
        logger.error(f"Validazione fallita: {ve}", exc_info=True)
        print(f"ERROR Validazione: {ve}")
        return _generate_error_report(str(ve), "Dati Invalidi")
    except Exception as e:
        # Altri errori
        import traceback
        error_msg = f"Errore process_all_funds: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Errore process_all_funds: {e}", exc_info=True)
        print(error_msg)
        return _generate_error_report(str(e), "Errore Elaborazione")
    
    # Validazione processed_data prima di create_comparison_dataframe
    try:
        if not processed_data:
            print("ERROR: processed_data vuoto dopo process_all_funds")
            return _generate_error_report("Nessun dato processato", "Errore Elaborazione")
        
        # Valida struttura processed_data
        for fund_name, fund_data in processed_data.items():
            normalized = fund_data.get('normalized_data')
            if normalized is None or normalized.empty:
                print(f"WARNING: {fund_name} non ha normalized_data")
                continue
            if 'Normalized_Value' not in normalized.columns:
                print(f"ERROR: {fund_name} normalized_data non ha colonna Normalized_Value")
                raise ValueError(f"Struttura dati invalida per {fund_name}")
            if not isinstance(normalized.index, pd.DatetimeIndex):
                print(f"ERROR: {fund_name} normalized_data non ha DatetimeIndex")
                raise ValueError(f"Indice dati invalido per {fund_name}")
        
        # Se tutte le validazioni passano, procedi
        comparison_df = processor.create_comparison_dataframe(processed_data)
        logger.info(f"create_comparison_dataframe completato, shape: {comparison_df.shape}")
        print(f"DEBUG: create_comparison_dataframe completato, shape: {comparison_df.shape}")
        
        if comparison_df.empty:
            print("WARNING: comparison_df vuoto dopo create_comparison_dataframe")
            return generate_empty_report()
        
    except ValueError as ve:
        import traceback
        error_msg = f"Errore create_comparison_dataframe: {str(ve)}\n{traceback.format_exc()}"
        logger.error(f"Errore create_comparison_dataframe: {ve}", exc_info=True)
        print(error_msg)
        return _generate_error_report(f"Errore creazione grafico: {str(ve)}", "Errore Grafico")
    except Exception as e:
        import traceback
        error_msg = f"Errore create_comparison_dataframe: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Errore create_comparison_dataframe: {e}", exc_info=True)
        print(error_msg)
        return _generate_error_report(f"Errore creazione grafico: {str(e)}", "Errore Grafico")
    
    # Genera report completo con strumenti manager incluso
    template_path = get_template_path()
    
    # Valida che template esista
    if not os.path.exists(template_path):
        print(f"ERROR: Template non trovato: {template_path}")
        return _generate_error_report(f"Template non trovato: {template_path}", "Errore Sistema")
    
    # Prepara strumenti per visualizer
    with instruments_lock:
        instruments_for_manager = current_instruments.copy()
    
    # Genera report con try-catch specifico
    try:
        report_html = visualizer.generate_full_report(
            comparison_df,
            processed_data,
            template_path
        )
        logger.info(f"generate_full_report completato, size: {len(report_html)} bytes")
        print(f"DEBUG: generate_full_report completato, size: {len(report_html)} bytes")
    except Exception as e:
        import traceback
        error_msg = f"Errore generate_full_report: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Errore generate_full_report: {e}", exc_info=True)
        print(error_msg)
        return _generate_error_report(f"Errore generazione report: {str(e)}", "Errore Report")
    
    # Aggiungi sezione gestione strumenti manualmente (per modalità interattiva)
    instrument_manager = visualizer.create_instrument_manager_section(instruments_for_manager)
    report_html = report_html.replace('{{INSTRUMENT_MANAGER}}', instrument_manager)
    
    # Aggiungi data generazione
    generation_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    report_html = report_html.replace('{{ datetime }}', generation_date)
    
    return report_html


def _generate_error_report(error_message: str, error_type: str = "Errore") -> str:
    """Genera report HTML con messaggio errore"""
    empty_report = generate_empty_report()
    
    error_html = f'''
    <div class="error-message" style="padding: 20px; background: #fee; border: 2px solid #f00; margin: 20px; border-radius: 8px;">
        <h3 style="color: #c00;">{error_type}</h3>
        <p><strong>Messaggio:</strong> {error_message}</p>
        <p><small>Controlla la console del server per dettagli tecnici.</small></p>
    </div>
    '''
    
    # Sostituisci INSTRUMENT_MANAGER con errore + manager
    with instruments_lock:
        instruments_for_manager = current_instruments.copy()
    instrument_manager = visualizer.create_instrument_manager_section(instruments_for_manager)
    empty_report = empty_report.replace('{{INSTRUMENT_MANAGER}}', error_html + instrument_manager)
    
    return empty_report


def generate_empty_report() -> str:
    """Genera report vuoto con solo interfaccia gestione"""
    try:
        template_path = get_template_path()
        
        if not os.path.exists(template_path):
            logger.error(f"Template non trovato: {template_path}")
            return f"<html><body><h1>Errore</h1><p>Template non trovato: {template_path}</p></body></html>"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Genera componenti vuoti
        empty_chart = '<div class="empty-state"><p>Nessun strumento selezionato. Aggiungi un ISIN o ticker per iniziare l\'analisi.</p></div>'
        empty_metrics = '<div class="empty-state"><p>Nessuna metrica disponibile.</p></div>'
        empty_description = '<div class="empty-state"><p>Nessuna descrizione disponibile.</p></div>'
        
        # Genera interfaccia gestione strumenti
        try:
            with instruments_lock:
                instruments_for_manager = current_instruments.copy()
            instrument_manager = visualizer.create_instrument_manager_section(instruments_for_manager)
        except Exception as e:
            logger.error(f"Errore creazione instrument manager: {e}", exc_info=True)
            instrument_manager = '<div class="error-message"><p>Errore caricamento gestione strumenti</p></div>'
        
        # Sostituisci placeholder
        report = template.replace('{{PERFORMANCE_CHART}}', empty_chart)
        report = report.replace('{{METRICS_TABLE}}', empty_metrics)
        report = report.replace('{{FUNDS_DESCRIPTION}}', empty_description)
        report = report.replace('{{EXECUTIVE_SUMMARY}}', '')
        report = report.replace('{{SECTOR_ANALYSIS}}', '')
        report = report.replace('{{PORTFOLIO_ANALYSIS}}', '')
        report = report.replace('{{TECHNICAL_INDICATORS}}', '')
        report = report.replace('{{ADVANCED_METRICS}}', '')
        report = report.replace('{{INSTRUMENT_MANAGER}}', instrument_manager)
        report = report.replace('{{COMPOSITION_SECTION}}', '')
        report = report.replace('{{RAW_DATA}}', '{}')
        
        # Branding
        import config
        report_config = config.REPORT_CONFIG
        report = report.replace('{{COMPANY_NAME}}', report_config.get('company_name', 'Analisi Fondi Healthcare'))
        report = report.replace('{{FOOTER_TEXT}}', report_config.get('footer_text', 'Report generato automaticamente'))
        report = report.replace('{{DISCLAIMER}}', report_config.get('disclaimer', ''))
        report = report.replace('{{ datetime }}', datetime.now().strftime('%d/%m/%Y %H:%M'))
        
        return report
    except Exception as e:
        import traceback
        error_msg = f"Errore generate_empty_report: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg, exc_info=True)
        return f"<html><body><h1>Errore</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>"


@app.route('/')
def index():
    """Serve report HTML"""
    try:
        logger.debug("index() chiamato")
        # Carica strumenti attuali
        with instruments_lock:
            instruments_list = list(current_instruments.values())
        
        logger.debug(f"index(): instruments_list length: {len(instruments_list)}")
        
        if not instruments_list:
            # Report vuoto
            logger.info("index(): Nessuno strumento, ritorna report vuoto")
            return generate_empty_report()
    except Exception as e:
        import traceback
        error_msg = f"Errore in index(): {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg, exc_info=True)
        return f"<html><body><h1>Errore</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>", 500
    
    # Prepara dati strumenti
    instruments_data = {}
    for instrument in instruments_list:
        isin = instrument.get('isin')
        if isin:
            # Recupera dati storici
            print(f"DEBUG index(): Recupero dati per {isin}...")
            historical = collector.get_historical_data(isin, years=config.YEARS_BACK)
            
            if historical is not None and not historical.empty:
                # VALIDAZIONE AGGIUNTIVA: Verifica che sia DataFrame valido
                if not isinstance(historical, pd.DataFrame):
                    print(f"ERROR: historical_data per {isin} non è DataFrame")
                    continue
                
                # VALIDAZIONE: Verifica DatetimeIndex
                if not isinstance(historical.index, pd.DatetimeIndex):
                    print(f"WARNING: historical_data per {isin} non ha DatetimeIndex, tenta fix...")
                    # Tenta fix (già gestito in normalize_to_base100, ma meglio validare qui)
                    if 'Date' in historical.columns:
                        historical['Date'] = pd.to_datetime(historical['Date'])
                        historical = historical.set_index('Date')
                        print(f"DEBUG: ✓ DatetimeIndex creato per {isin}")
                    else:
                        print(f"ERROR: Impossibile creare DatetimeIndex per {isin}")
                        continue
                
                # VALIDAZIONE: Verifica colonna Price o Close
                if 'Price' not in historical.columns and 'Close' not in historical.columns:
                    print(f"ERROR: historical_data per {isin} non ha colonna Price o Close")
                    continue
                
                # Validazione e normalizzazione name_short
                name_short = instrument.get('name_short') or instrument.get('name') or isin
                if not name_short or not isinstance(name_short, str) or name_short.strip() == '':
                    print(f"ERROR: Nome non valido per strumento {isin}")
                    print(f"  name_short: {instrument.get('name_short')}")
                    print(f"  name: {instrument.get('name')}")
                    print(f"  isin: {isin}")
                    continue
                
                # Verifica che non ci siano chiavi duplicate
                if name_short in instruments_data:
                    print(f"WARNING: Chiave duplicata '{name_short}', uso '{isin}' come chiave univoca")
                    name_short = f"{name_short}_{isin}"
                
                # Recupera descrizione
                description, description_source = collector.get_fund_description(
                    isin,
                    ticker=instrument.get('ticker'),
                    name=name_short
                )
                
                print(f"DEBUG: ✓ Dati validi per {isin}, aggiunto come '{name_short}'")
                
                # Struttura allineata a main.py
                instruments_data[name_short] = {
                    'isin': isin,
                    'ticker': instrument.get('ticker'),  # Opzionale, può essere None
                    'name_short': name_short,  # Usa valore validato
                    'historical_data': historical,  # DataFrame validato
                    'composition': {},  # Opzionale, può essere vuoto
                    'description': description,
                    'description_source': description_source
                }
            else:
                print(f"DEBUG: ✗ Nessun dato disponibile per {isin}")
    
    # Validazione esplicita dopo il loop
    print(f"DEBUG index(): instruments_data keys: {list(instruments_data.keys())}")
    print(f"DEBUG index(): instruments_data empty: {len(instruments_data) == 0}")
    
    if len(instruments_data) == 0:
        print("WARNING: Nessun dato disponibile per gli strumenti selezionati")
        for instrument in instruments_list:
            isin = instrument.get('isin', 'N/A')
            print(f"  - {isin}: dati non recuperati")
        return generate_empty_report()
    
    return generate_report_html(instruments_data)


@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Restituisce lista strumenti attuali"""
    with instruments_lock:
        instruments_list = list(current_instruments.values())
    return jsonify({
        'instruments': instruments_list,
        'count': len(instruments_list)
    })


@app.route('/api/add_instrument', methods=['POST'])
def add_instrument():
    """Aggiunge un nuovo strumento"""
    data = request.get_json()
    identifier = data.get('isin') or data.get('ticker', '').strip()
    
    if not identifier:
        return jsonify({'error': 'ISIN o Ticker richiesto'}), 400
    
    # Verifica se già presente
    with instruments_lock:
        if identifier in current_instruments:
            return jsonify({'error': 'Strumento già presente'}), 400
    
    # Prova a recuperare metadati
    try:
        # Se è un ISIN, usa fund_manager se disponibile
        if len(identifier) >= 12 and identifier[:2].isalpha() and fund_manager:
            try:
                print(f"DEBUG: Tentativo recupero metadati per ISIN {identifier}")
                fund_info = fund_manager.add_fund_by_isin(identifier, auto_fetch_metadata=True)
                
                if fund_info and fund_info.get('name_short'):
                    isin = identifier
                    ticker = fund_info.get('ticker', identifier)
                    name = fund_info.get('name_short', identifier)
                    print(f"DEBUG: Metadati recuperati: name={name}, ticker={ticker}")
                else:
                    print(f"WARNING: Metadati non disponibili per {identifier}, uso come ticker")
                    ticker = identifier
                    isin = identifier
                    name = identifier
            except Exception as e:
                print(f"WARNING: Errore recupero metadati per {identifier}: {e}")
                # Fallback: tratta come ticker
                ticker = identifier
                isin = identifier
                name = identifier
        elif len(identifier) >= 12 and identifier[:2].isalpha() and not fund_manager:
            print(f"WARNING: fund_manager non disponibile, tratta {identifier} come ticker")
            ticker = identifier
            isin = identifier
            name = identifier
        else:
            # Probabilmente ticker
            ticker = identifier
            isin = identifier  # Usa identifier come ISIN anche se è ticker
            name = identifier
        
        # Verifica che i dati siano disponibili
        test_isin = isin or ticker
        print(f"DEBUG: Test recupero dati per {test_isin}...")
        
        try:
            test_data = collector.get_historical_data(test_isin, years=1)  # Test con 1 anno
            
            if test_data is None:
                print(f"ERROR: get_historical_data() restituito None per {test_isin}")
                return jsonify({'error': f'Dati non disponibili per {identifier} (None restituito)'}), 404
            
            if not isinstance(test_data, pd.DataFrame):
                print(f"ERROR: get_historical_data() restituito tipo non DataFrame: {type(test_data)}")
                return jsonify({'error': f'Dati non disponibili per {identifier} (formato invalido)'}), 404
            
            if test_data.empty:
                print(f"ERROR: get_historical_data() restituito DataFrame vuoto per {test_isin}")
                return jsonify({'error': f'Dati non disponibili per {identifier} (nessun dato storico)'}), 404
            
            print(f"DEBUG: ✓ Dati disponibili per {test_isin}: {len(test_data)} righe")
            
        except Exception as e:
            import traceback
            print(f"ERROR: Eccezione durante get_historical_data per {test_isin}: {e}")
            print(traceback.format_exc())
            return jsonify({'error': f'Errore recupero dati per {identifier}: {str(e)}'}), 500
        
        # Aggiungi strumento
        with instruments_lock:
            instrument_info = {
                'isin': isin or ticker,
                'ticker': ticker,
                'name': name or ticker,
                'name_short': name or ticker,
                'added_at': datetime.now().isoformat()
            }
            current_instruments[identifier] = instrument_info
        
        return jsonify({
            'success': True,
            'instrument': instrument_info,
            'message': f'Strumento {identifier} aggiunto con successo'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"add_instrument() errore per {identifier}: {e}", exc_info=True)
        print(f"ERROR add_instrument per {identifier}:")
        print(f"  Tipo errore: {type(e).__name__}")
        print(f"  Messaggio: {str(e)}")
        print(f"  Traceback completo:\n{error_details}")
        
        return jsonify({
            'error': f'Errore aggiunta strumento: {str(e)}',
            'details': error_details if app.debug else None
        }), 500


@app.route('/api/remove_instrument', methods=['POST'])
def remove_instrument():
    """Rimuove uno strumento"""
    data = request.get_json()
    identifier = data.get('isin') or data.get('ticker', '').strip()
    
    if not identifier:
        return jsonify({'error': 'ISIN o Ticker richiesto'}), 400
    
    with instruments_lock:
        if identifier not in current_instruments:
            return jsonify({'error': 'Strumento non trovato'}), 404
        
        del current_instruments[identifier]
    
    return jsonify({
        'success': True,
        'message': f'Strumento {identifier} rimosso con successo'
    })


@app.route('/api/clear_all', methods=['POST'])
def clear_all():
    """Rimuove tutti gli strumenti"""
    with instruments_lock:
        count = len(current_instruments)
        current_instruments.clear()
    
    return jsonify({
        'success': True,
        'message': f'{count} strumenti rimossi'
    })


@app.route('/api/regenerate', methods=['POST'])
def regenerate():
    """Rigenera report con strumenti attuali"""
    # Il report viene rigenerato automaticamente quando si accede a /
    return jsonify({
        'success': True,
        'message': 'Report rigenerato'
    })


def run_server(host='127.0.0.1', port=5000, open_browser=True):
    """Avvia server Flask"""
    url = f'http://{host}:{port}'
    print(f"\n{'=' * 60}")
    print("SERVER INTERATTIVO AVVIATO")
    print(f"{'=' * 60}")
    print(f"\nServer disponibile su: {url}")
    print(f"\nPremi CTRL+C per fermare il server\n")
    
    if open_browser:
        # Apri browser dopo 1 secondo
        def open_browser_delayed():
            import time
            time.sleep(1)
            webbrowser.open(url)
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    run_server()
