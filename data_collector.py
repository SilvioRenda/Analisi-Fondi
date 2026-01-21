"""
Modulo per la raccolta dati storici e composizione dei fondi
"""

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
import config
from fund_manager import FundManager
from data_validator import DataValidator


class DataCollector:
    """Raccoglie dati storici e composizione dei fondi"""
    
    def __init__(self):
        self.cache_dir = config.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.fund_manager = FundManager()
        self.validator = DataValidator()
        self.validator = DataValidator()
        
    def _get_cache_path(self, isin: str, data_type: str) -> str:
        """Genera il percorso del file di cache"""
        return os.path.join(self.cache_dir, f"{isin}_{data_type}.json")
    
    def _save_description_cache(self, isin: str, description: str, source: str):
        """Salva descrizione in cache"""
        cache_path = self._get_cache_path(isin, "description")
        cache_data = {
            'description': description,
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, default=str)
    
    def _load_description_cache(self, isin: str) -> Optional[Tuple[str, str]]:
        """
        Carica descrizione dalla cache se disponibile e recente (max 7 giorni)
        
        Returns:
            Tupla (descrizione, fonte) o None se non disponibile o scaduta
        """
        cache_path = self._get_cache_path(isin, "description")
        if os.path.exists(cache_path):
            file_time = os.path.getmtime(cache_path)
            # TTL: 7 giorni (descrizioni cambiano meno frequentemente dei prezzi)
            if (datetime.now() - datetime.fromtimestamp(file_time)).days < 7:
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                    return (cached.get('description'), cached.get('source', ''))
                except:
                    pass
        return None
    
    def _load_cache(self, cache_path: str) -> Optional[dict]:
        """Carica dati dalla cache se disponibili e recenti (max 24h)"""
        if os.path.exists(cache_path):
            file_time = os.path.getmtime(cache_path)
            if (datetime.now() - datetime.fromtimestamp(file_time)).days < 1:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None
    
    def _save_cache(self, cache_path: str, data: dict):
        """Salva dati nella cache"""
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _is_us_mutual_fund(self, isin: str, ticker: str = None) -> bool:
        """
        Determina se è un mutual fund USA
        
        I mutual funds USA hanno:
        - ISIN che inizia con 'US'
        - Ticker di 5 lettere che finisce in 'X' (es. PRHSX, VFINX, FXAIX)
        
        Args:
            isin: ISIN del fondo
            ticker: Ticker del fondo (opzionale)
            
        Returns:
            True se è un mutual fund USA, False altrimenti
        """
        # Controlla ISIN
        if isin and isin.startswith('US'):
            return True
        
        # Controlla ticker (5 lettere che finisce in X)
        if ticker and len(ticker) == 5 and ticker.endswith('X'):
            return True
        
        return False
    
    def _isin_to_ticker(self, isin: str) -> Optional[str]:
        """
        Tenta di convertire ISIN a ticker Yahoo Finance
        Per fondi europei, il formato è spesso ISIN.Exchange o ticker specifici
        """
        # Mapping manuale per alcuni fondi noti (da aggiornare con ticker reali se disponibili)
        isin_to_ticker_map = {
            "LU0097089360": None,  # Alliance Bernstein
            "LU1960219225": None,  # BlackRock
            "LU0823417067": None,  # BNP Paribas
            "IE0003111113": None,  # Wellington
            "LU2400458779": None,  # Robeco
            "LU2078916223": None,  # Fidelity
            "LU0188500879": None,  # Pictet
            "IE00BKSBD728": None,  # Polar Capital
            "US87281Y1029": "PRHSX",  # T. Rowe Price Health Sciences
        }
        
        if isin in isin_to_ticker_map:
            return isin_to_ticker_map[isin]
        
        # Per fondi europei, prova formato ISIN.Exchange
        # Yahoo Finance usa spesso questo formato per fondi UCITS
        return None  # Torneremo a provare con ISIN diretto nel metodo get_historical_data
    
    def _get_figi_metadata(self, isin: str) -> Dict:
        """
        Recupera metadati da Open FIGI usando ISIN
        Ritorna dizionario con nome, ticker, exchange, etc.
        """
        try:
            url = f"{config.OPEN_FIGI_BASE_URL}/mapping"
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = [{
                "idType": "ID_ISIN",
                "idValue": isin
            }]
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and len(data[0].get('data', [])) > 0:
                    figi_data = data[0]['data'][0]
                    return {
                        'name': figi_data.get('name', ''),
                        'ticker': figi_data.get('ticker', ''),
                        'exchange': figi_data.get('exchCode', ''),
                        'market_sector': figi_data.get('marketSector', ''),
                        'security_type': figi_data.get('securityType', ''),
                        'figi': figi_data.get('figi', ''),
                        'composite_figi': figi_data.get('compositeFIGI', '')
                    }
        except Exception as e:
            print(f"  Errore recupero metadati Open FIGI per {isin}: {e}")
        
        return {}
    
    def _get_fund_info_from_yahoo(self, ticker: str) -> Dict:
        """
        Recupera informazioni dettagliate del fondo da Yahoo Finance
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            result = {
                'sectors': {},
                'top_holdings': []
            }
            
            # Settori
            if 'sector' in info and info['sector']:
                result['sectors'][info['sector']] = 100.0
            
            # Top holdings - prova diversi campi
            if 'holdings' in info and info['holdings']:
                result['top_holdings'] = info['holdings']
            elif 'topHoldings' in info and info['topHoldings']:
                result['top_holdings'] = info['topHoldings']
            elif 'majorHoldings' in info and info['majorHoldings']:
                result['top_holdings'] = info['majorHoldings']
            
            return result
        except:
            return {'sectors': {}, 'top_holdings': []}
    
    def _calculate_adj_close_manual(self, close: pd.Series, dividends: pd.Series, 
                                     capital_gains: pd.Series) -> pd.Series:
        """
        Calcola Adj Close manualmente quando Yahoo Finance non lo fornisce
        
        IMPORTANTE: Per mutual funds, quando c'è una distribuzione, il prezzo Close può:
        - Scendere (ex-dividend): Close[t] < Close[t-1]
        - Salire (già adjusted o per altri motivi): Close[t] > Close[t-1]
        
        La formula corretta calcola Adj Close in modo che elimini i salti:
        - Se c'è distribuzione E Close[t] < Close[t-1]: Close[t] è ex-dividend, aggiungi distribuzione
        - Se c'è distribuzione E Close[t] >= Close[t-1]: Close[t] potrebbe già essere adjusted, usa direttamente
        - Se non c'è distribuzione: variazione normale
        
        Formula ottimizzata:
        - Se distribuzione > 0: Adj_Close[t] = Adj_Close[t-1] * max(Close[t] / Close[t-1], (Close[t] + Dist[t]) / Close[t-1])
        - Se distribuzione = 0: Adj_Close[t] = Adj_Close[t-1] * (Close[t] / Close[t-1])
        
        Args:
            close: Serie con prezzi Close
            dividends: Serie con dividendi
            capital_gains: Serie con capital gains
            
        Returns:
            Serie con Adj Close calcolato
        """
        if close is None or close.empty:
            return pd.Series(dtype=float)
        
        adj_close = pd.Series(index=close.index, dtype=float)
        adj_close.iloc[0] = close.iloc[0]
        
        # Combina dividendi e capital gains
        distributions = dividends.fillna(0) + capital_gains.fillna(0)
        
        for i in range(1, len(close)):
            prev_close = close.iloc[i-1]
            curr_close = close.iloc[i]
            distribution = distributions.iloc[i]
            
            if pd.notna(prev_close) and prev_close != 0 and pd.notna(curr_close):
                if distribution > 0:
                    # C'è una distribuzione
                    # IMPORTANTE: Per mutual funds, Yahoo Finance può fornire dati inconsistenti.
                    # Se Close aumenta quando c'è distribuzione, potrebbe essere:
                    # 1. Prezzo già adjusted (ma inconsistente)
                    # 2. Performance positiva del fondo
                    # 3. Dati errati di Yahoo Finance
                    
                    price_change_pct = (curr_close - prev_close) / prev_close
                    distribution_pct = distribution / prev_close
                    
                    if price_change_pct < -0.01:  # Prezzo è sceso di >1% (probabilmente ex-dividend)
                        # Prezzo è ex-dividend: aggiungi distribuzione per ottenere prezzo con distribuzione reinvestita
                        total_value = curr_close + distribution
                        daily_return = total_value / prev_close
                    else:
                        # Prezzo è aumentato o stabile quando c'è distribuzione
                        # Questo può indicare:
                        # 1. Prezzo già adjusted (anche se inconsistente)
                        # 2. Performance positiva del fondo
                        # 3. Dati inconsistenti di Yahoo Finance
                        # In tutti i casi, usa solo Close senza aggiungere distribuzione
                        # per evitare doppio conteggio o salti eccessivi
                        daily_return = curr_close / prev_close
                else:
                    # Nessuna distribuzione: variazione normale
                    daily_return = curr_close / prev_close
                
                # Adj Close cumulativo
                adj_close.iloc[i] = adj_close.iloc[i-1] * daily_return
            else:
                # Gestisci valori NaN o zero
                adj_close.iloc[i] = adj_close.iloc[i-1] if i > 0 else curr_close
        
        return adj_close
    
    def _get_yahoo_data_smart(self, ticker_str: str, start_date: datetime, end_date: datetime, 
                              is_us_mutual_fund: bool = False) -> Optional[pd.DataFrame]:
        """
        Recupera dati da Yahoo Finance in modo intelligente
        
        Per mutual funds USA:
        - Usa Adj Close (già include dividendi e capital gains reinvestiti)
        - Marca _is_adjusted = True
        
        Per altri strumenti (ETF, fondi EU, azioni):
        - Usa Close + Dividends/Capital Gains separati
        - Marca _is_adjusted = False
        
        Args:
            ticker_str: Ticker o identificatore Yahoo Finance
            start_date: Data di inizio
            end_date: Data di fine
            is_us_mutual_fund: True se è un mutual fund USA
            
        Returns:
            DataFrame con colonne Price, Dividends, Capital Gains, _is_adjusted
            oppure None se errore
        """
        try:
            stock = yf.Ticker(ticker_str)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            if is_us_mutual_fund:
                # Per mutual funds USA: usa Adj Close (già adjusted per dividendi)
                if 'Adj Close' not in hist.columns:
                    # Adj Close non disponibile: calcolalo manualmente
                    # Questo elimina i salti causati dalle distribuzioni
                    close_series = hist['Close']
                    dividends_series = hist['Dividends'] if 'Dividends' in hist.columns else pd.Series(0.0, index=hist.index)
                    capital_gains_series = hist['Capital Gains'] if 'Capital Gains' in hist.columns else pd.Series(0.0, index=hist.index)
                    
                    # Calcola Adj Close manualmente
                    adj_close_calculated = self._calculate_adj_close_manual(close_series, dividends_series, capital_gains_series)
                    
                    # Usa Adj Close calcolato come Price
                    data = pd.DataFrame({
                        'Price': adj_close_calculated,
                        'Dividends': 0.0,  # Già inclusi in Adj Close calcolato
                        'Capital Gains': 0.0,  # Già inclusi in Adj Close calcolato
                        '_is_adjusted': True  # Adj Close calcolato include dividendi reinvestiti
                    })
                else:
                    price_col = 'Adj Close'
                    # IMPORTANTE: Adj Close già include dividendi e capital gains reinvestiti
                    # NON aggiungere Dividends/Capital Gains separatamente per evitare doppio conteggio
                    data = pd.DataFrame({
                        'Price': hist[price_col],
                        'Dividends': 0.0,  # Già inclusi in Adj Close
                        'Capital Gains': 0.0,  # Già inclusi in Adj Close
                        '_is_adjusted': True  # Adj Close già include dividendi reinvestiti
                    })
            else:
                # Per altri strumenti (ETF, fondi EU, azioni): usa Close + Dividends separati
                data = pd.DataFrame({
                    'Price': hist['Close'],
                    'Dividends': hist['Dividends'] if 'Dividends' in hist.columns else 0.0,
                    'Capital Gains': hist['Capital Gains'] if 'Capital Gains' in hist.columns else 0.0,
                    '_is_adjusted': False  # Close non include dividendi, vanno aggiunti manualmente
                })

            # Assicura che Dividends e Capital Gains siano float e riempi NaN con 0
            if 'Dividends' in data.columns:
                data['Dividends'] = data['Dividends'].fillna(0.0).astype(float)
            else:
                data['Dividends'] = 0.0

            if 'Capital Gains' in data.columns:
                data['Capital Gains'] = data['Capital Gains'].fillna(0.0).astype(float)
            else:
                data['Capital Gains'] = 0.0

            return data
            
        except Exception as e:
            # Silently fail, useremo altre fonti
            return None
    
    def get_historical_data(self, isin: str, years: int = 5) -> Optional[pd.DataFrame]:
        """
        Recupera dati storici per un fondo
        Prova multiple fonti in ordine: Yahoo Finance -> Exchange codes -> Web scraping
        """
        cache_path = self._get_cache_path(isin, "historical")
        cached = self._load_cache(cache_path)
        if cached:
            try:
                from io import StringIO
                df = pd.read_json(StringIO(cached['data']), orient='records')
                # Ricostruisci DatetimeIndex dalla colonna Date se presente
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                elif 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                else:
                    # Fallback per cache vecchie senza colonna Date: crea DatetimeIndex approssimativo
                    # (non ideale, ma meglio di RangeIndex)
                    df.index = pd.date_range(start=datetime.now() - pd.Timedelta(days=len(df)), 
                                            periods=len(df), freq='D')
                
                # Aggiungi _is_adjusted se mancante (per compatibilità con cache vecchie)
                if '_is_adjusted' not in df.columns:
                    # Determina se adjusted in base alla fonte salvata
                    source = cached.get('source', '')
                    if any(adj_source in source for adj_source in ['EOD Historical Data', 'Alpha Vantage', 'Financial Modeling Prep']):
                        df['_is_adjusted'] = True
                    else:
                        # Yahoo Finance o altre fonti = unadjusted
                        df['_is_adjusted'] = False

                # Assicura che Dividends e Capital Gains siano sempre presenti
                if 'Dividends' not in df.columns:
                    # Se mancano, aggiungi basandoti su _is_adjusted
                    if df.get('_is_adjusted', False) if '_is_adjusted' in df.columns else False:
                        df['Dividends'] = 0.0  # Prezzi adjusted, dividendi già inclusi
                    else:
                        df['Dividends'] = 0.0  # Default a 0 se non disponibili

                if 'Capital Gains' not in df.columns:
                    if df.get('_is_adjusted', False) if '_is_adjusted' in df.columns else False:
                        df['Capital Gains'] = 0.0  # Prezzi adjusted, capital gains già inclusi
                    else:
                        df['Capital Gains'] = 0.0  # Default a 0 se non disponibili

                return df
            except Exception as e:
                # Fallback: prova a leggere come stringa JSON diretta
                try:
                    df = pd.read_json(cached['data'], orient='records')
                    # Ricostruisci DatetimeIndex dalla colonna Date se presente
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
                        df = df.set_index('Date')
                    elif 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                    else:
                        # Fallback per cache vecchie senza colonna Date: crea DatetimeIndex approssimativo
                        df.index = pd.date_range(start=datetime.now() - pd.Timedelta(days=len(df)), 
                                                periods=len(df), freq='D')
                    
                    # Aggiungi _is_adjusted se mancante
                    if '_is_adjusted' not in df.columns:
                        source = cached.get('source', '')
                        if any(adj_source in source for adj_source in ['EOD Historical Data', 'Alpha Vantage', 'Financial Modeling Prep']):
                            df['_is_adjusted'] = True
                        else:
                            df['_is_adjusted'] = False

                    # Assicura che Dividends e Capital Gains siano sempre presenti
                    if 'Dividends' not in df.columns:
                        if df.get('_is_adjusted', False) if '_is_adjusted' in df.columns else False:
                            df['Dividends'] = 0.0
                        else:
                            df['Dividends'] = 0.0

                    if 'Capital Gains' not in df.columns:
                        if df.get('_is_adjusted', False) if '_is_adjusted' in df.columns else False:
                            df['Capital Gains'] = 0.0
                        else:
                            df['Capital Gains'] = 0.0

                    return df
                except:
                    return None
        
        ticker = self._isin_to_ticker(isin)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        # Prova diversi metodi per recuperare i dati
        data = None
        source_used = None
        
        # Metodo 0: Prova EOD Historical Data API (se disponibile)
        if config.EOD_API_KEY:
            data = self._get_eod_total_return(isin, start_date, end_date)
            if data is not None and not data.empty:
                source_used = "EOD Historical Data API"
        
        # Metodo 1: Prova con ticker se disponibile
        if ticker:
            # Determina se è un mutual fund USA
            is_us_mutual_fund = self._is_us_mutual_fund(isin, ticker)
            
            # Usa funzione smart che gestisce adjusted/unadjusted correttamente
            data = self._get_yahoo_data_smart(ticker, start_date, end_date, is_us_mutual_fund)
            if data is not None and not data.empty:
                source_used = f"Yahoo Finance (ticker: {ticker})"
        
        # Metodo 2: Prova con ISIN diretto e vari exchange
        if data is None or data.empty:
            try:
                # Per fondi europei UCITS, prova formato ISIN.Exchange
                # Exchange codes: PA=Paris, DE=XETRA, L=London, MI=Milan, AS=Amsterdam, SW=Swiss, IR=Irlanda
                exchanges = ['L', 'PA', 'DE', 'MI', 'AS', 'SW', 'BR', 'VI', 'IR', 'LN', 'LS']
                # Determina se è un mutual fund USA (non dovrebbe essere per questo metodo, ma per sicurezza)
                is_us_mutual_fund = self._is_us_mutual_fund(isin, ticker)
                
                for exchange in exchanges:
                    try:
                        ticker_str = f"{isin}.{exchange}"
                        # Usa funzione smart che gestisce adjusted/unadjusted correttamente
                        data = self._get_yahoo_data_smart(ticker_str, start_date, end_date, is_us_mutual_fund)
                        if data is not None and not data.empty and len(data) > 10:  # Almeno 10 giorni di dati
                            source_used = f"Yahoo Finance ({ticker_str})"
                            print(f"  ✓ Dati trovati con {ticker_str}")
                            break
                    except:
                        continue
                
                # Se ancora non trovato, prova ISIN diretto
                if (data is None or data.empty) and len(isin) > 0:
                    try:
                        # Usa funzione smart che gestisce adjusted/unadjusted correttamente
                        data = self._get_yahoo_data_smart(isin, start_date, end_date, is_us_mutual_fund)
                        if data is not None and not data.empty and len(data) > 10:
                            source_used = "Yahoo Finance (ISIN diretto)"
                            print(f"  ✓ Dati trovati con ISIN diretto")
                    except:
                        pass
            except Exception as e:
                print(f"  ⚠ Errore con ISIN {isin}: {e}")
        
        # Metodo 3: Prova con exchange code IR (Irlanda) per fondi IE (prima dello scraping)
        if data is None or data.empty and isin.startswith('IE'):
            try:
                ticker_str = f"{isin}.IR"
                # Usa funzione smart che gestisce adjusted/unadjusted correttamente
                # I fondi IE non sono mutual funds USA, quindi is_us_mutual_fund = False
                data = self._get_yahoo_data_smart(ticker_str, start_date, end_date, False)
                if data is not None and not data.empty and len(data) > 10:
                    source_used = f"Yahoo Finance ({ticker_str})"
                    print(f"  ✓ Dati trovati con {ticker_str}")
            except:
                pass
        
        # Metodo 4: Web scraping da Morningstar, Finanzen.net e altre fonti (fallback)
        if data is None or data.empty:
            data = self._scrape_historical_data(isin, start_date, end_date)
        
        if data is not None and not data.empty:
            # Valida dati prima di salvare
            is_valid, validation_results = self.validator.validate_data(data)
            
            if not is_valid:
                # Dati non validi, logga warning ma usa comunque (potrebbe essere l'unica fonte)
                warnings = [f"{k}: {v['message']}" for k, v in validation_results.items() if not v['valid']]
                print(f"  [WARN] Dati con problemi di validazione: {', '.join(warnings)}")
            
            # Salva in cache con informazioni sulla fonte
            # IMPORTANTE: Includere l'indice DatetimeIndex come colonna 'Date' per preservarlo
            data_to_save = data.copy()
            if isinstance(data_to_save.index, pd.DatetimeIndex):
                # Aggiungi l'indice come colonna 'Date' prima di salvare
                data_to_save['Date'] = data_to_save.index
                # Reset index per avere Date come colonna normale nel JSON
                data_to_save = data_to_save.reset_index(drop=True)
            
            cache_data = {
                'data': data_to_save.to_json(orient='records', date_format='iso'),
                'timestamp': datetime.now().isoformat(),
                'source': source_used or 'Unknown',
                'validation': validation_results
            }
            self._save_cache(cache_path, cache_data)
            if source_used:
                print(f"  Fonte dati: {source_used}")
        else:
            print(f"  ATTENZIONE: Nessun dato trovato per ISIN {isin} da nessuna fonte disponibile")
        
        return data
    
    def _scrape_historical_data(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Web scraping per dati storici (fallback)
        Prova Morningstar, Finanzen.net e altre fonti europee
        """
        print(f"Tentativo scraping per ISIN {isin}...")
        
        # Metodo 1: Morningstar
        data = self._scrape_morningstar(isin, start_date, end_date)
        if data is not None and not data.empty:
            print(f"  ✓ Dati trovati su Morningstar")
            return data
        
        # Metodo 2: Finanzen.net (per fondi europei)
        data = self._scrape_finanzen(isin, start_date, end_date)
        if data is not None and not data.empty:
            print(f"  ✓ Dati trovati su Finanzen.net")
            return data
        
        # Metodo 3: JustETF (per ETF e fondi)
        data = self._scrape_justetf(isin, start_date, end_date)
        if data is not None and not data.empty:
            print(f"  ✓ Dati trovati su JustETF")
            return data
        
        return None
    
    def _get_eod_total_return(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Recupera Total Return adjusted da EOD Historical Data API
        EOD fornisce dati già adjusted per total return
        """
        if not config.EOD_API_KEY:
            return None
        
        try:
            # EOD usa formato: {exchange}.{ticker} o ISIN diretto
            # Per fondi, prova prima con ISIN
            url = f"https://eodhistoricaldata.com/api/eod/{isin}"
            params = {
                'api_token': config.EOD_API_KEY,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'period': 'd',
                'fmt': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data_json = response.json()
                if data_json and len(data_json) > 0:
                    # EOD restituisce dati già adjusted per total return
                    df = pd.DataFrame(data_json)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    df = df.sort_index()
                    
                    # EOD fornisce 'adjusted_close' che include dividendi reinvestiti
                    if 'adjusted_close' in df.columns:
                        result = pd.DataFrame({
                            'Price': df['adjusted_close'],
                            'Dividends': 0.0,  # Già inclusi in adjusted_close
                            'Capital Gains': 0.0,  # Già inclusi in adjusted_close
                            '_is_adjusted': True  # Prezzi adjusted (include dividendi reinvestiti)
                        })
                        return result
                    elif 'close' in df.columns:
                        # Se non c'è adjusted_close, usa close (ma non è ideale)
                        result = pd.DataFrame({
                            'Price': df['close'],
                            'Dividends': 0.0,  # Non disponibile da EOD in questo caso
                            'Capital Gains': 0.0,  # Non disponibile da EOD in questo caso
                            '_is_adjusted': False  # Close non include dividendi
                        })
                        return result
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _get_alpha_vantage_adjusted(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Recupera dati adjusted (total return) da Alpha Vantage API
        Alpha Vantage fornisce adjusted_close che include dividendi reinvestiti
        
        IMPORTANTE: I prezzi restituiti sono ADJUSTED (includono dividendi reinvestiti).
        Il DataFrame restituito avrà colonna '_is_adjusted = True' per evitare doppio conteggio.
        Non aggiungere manualmente dividendi a questi prezzi.
        
        NOTA IMPORTANTE: 
        - TIME_SERIES_DAILY_ADJUSTED è un endpoint PREMIUM (richiede abbonamento)
        - Il piano gratuito supporta solo TIME_SERIES_DAILY (senza adjusted close)
        - Quindi questo metodo NON funziona con il piano gratuito
        - Per Total Return, è necessario un piano premium o usare altre fonti
        
        Nota: Alpha Vantage richiede 1 secondo tra le richieste (rate limit)
        """
        if not config.ALPHA_VANTAGE_API_KEY:
            return None
        
        try:
            # Alpha Vantage usa ticker, non ISIN direttamente
            # Per fondi comuni, potrebbe essere necessario il ticker
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'apikey': config.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'  # full per dati storici completi
            }
            
            # Alpha Vantage richiede 1 secondo tra le richieste
            time.sleep(1)
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data_json = response.json()
                
                # Alpha Vantage restituisce dati in formato specifico
                if 'Time Series (Daily)' in data_json:
                    time_series = data_json['Time Series (Daily)']
                    
                    # Converti in DataFrame
                    records = []
                    for date_str, values in time_series.items():
                        date = pd.to_datetime(date_str)
                        if start_date <= date <= end_date:
                            # Alpha Vantage usa '5. adjusted close' per adjusted close
                            adj_close = float(values.get('5. adjusted close', values.get('4. close', 0)))
                            records.append({
                                'date': date,
                                'Price': adj_close
                            })
                    
                    if records:
                        df = pd.DataFrame(records)
                        df = df.set_index('date')
                        df = df.sort_index()
                        # Alpha Vantage fornisce prezzi adjusted (include dividendi reinvestiti)
                        df['Dividends'] = 0.0  # Già inclusi in adjusted close
                        df['Capital Gains'] = 0.0  # Già inclusi in adjusted close
                        df['_is_adjusted'] = True
                        return df
                elif 'Error Message' in data_json:
                    # Alpha Vantage restituisce errore (es. simbolo non trovato)
                    error_msg = data_json.get('Error Message', '')
                    if 'Invalid API call' in error_msg or 'symbol' in error_msg.lower():
                        # Simbolo non supportato (probabilmente fondo comune)
                        return None
                elif 'Note' in data_json:
                    # Rate limit raggiunto - aspetta e riprova una volta
                    note = data_json.get('Note', '')
                    if 'API call frequency' in note:
                        time.sleep(2)  # Aspetta 2 secondi extra
                        # Non riprovare automaticamente per evitare loop
                        return None
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _get_fmp_historical(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Recupera dati storici da Financial Modeling Prep API
        FMP supporta alcuni ISIN per fondi
        
        IMPORTANTE: I prezzi restituiti sono ADJUSTED (adjClose include dividendi reinvestiti).
        Il DataFrame restituito avrà colonna '_is_adjusted = True' per evitare doppio conteggio.
        Non aggiungere manualmente dividendi a questi prezzi.
        """
        if not config.FMP_API_KEY:
            return None
        
        try:
            # FMP supporta ISIN per alcuni fondi
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{isin}"
            params = {
                'apikey': config.FMP_API_KEY,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data_json = response.json()
                
                if 'historical' in data_json and len(data_json['historical']) > 0:
                    # FMP restituisce dati in formato specifico
                    records = []
                    for item in data_json['historical']:
                        date = pd.to_datetime(item['date'])
                        # FMP fornisce 'adjClose' che include dividendi
                        records.append({
                            'date': date,
                            'Price': float(item.get('adjClose', item.get('close', 0)))
                        })
                    
                    if records:
                        df = pd.DataFrame(records)
                        df = df.set_index('date')
                        df = df.sort_index()
                        # FMP fornisce prezzi adjusted (adjClose include dividendi reinvestiti)
                        df['Dividends'] = 0.0  # Già inclusi in adjClose
                        df['Capital Gains'] = 0.0  # Già inclusi in adjClose
                        df['_is_adjusted'] = True
                        return df
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _scrape_morningstar(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Scraping dati storici da Morningstar
        """
        try:
            # URL Morningstar per la pagina del fondo
            url = f"https://www.morningstar.it/it/funds/snapshot/snapshot.aspx?id={isin}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.morningstar.it/'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Verifica se il fondo esiste
                title = soup.find('title')
                if title and ('not found' in title.text.lower() or 'errore' in title.text.lower()):
                    return None
                
                # Cerca link alla pagina performance/chart
                # Morningstar ha dati storici ma richiede navigazione più complessa
                # Per ora restituiamo None - servirebbe analisi più approfondita della struttura
                # o uso di API Morningstar (a pagamento)
                return None
        except Exception as e:
            pass
        
        return None
    
    def _scrape_finanzen(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Scraping dati storici da Finanzen.net (popolare per fondi europei)
        """
        try:
            url = f"https://www.finanzen.net/fonds/{isin}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Cerca dati storici nella pagina
                # Finanzen.net ha spesso grafici interattivi con dati JSON embedded
                # Cerca script tags con dati JSON
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'chart' in script.string.lower():
                        # Potrebbe contenere dati storici in formato JSON
                        # Richiede parsing più complesso
                        pass
                
                # Per ora restituiamo None - richiede analisi più approfondita
                return None
        except Exception as e:
            pass
        
        return None
    
    def get_benchmark_data(self, benchmark_ticker: str, years: int = 5) -> Optional[pd.DataFrame]:
        """
        Recupera dati storici del benchmark (SPY o EZU) con cache
        
        Args:
            benchmark_ticker: Ticker del benchmark ('SPY' o 'EZU')
            years: Numero di anni di dati storici da recuperare
            
        Returns:
            DataFrame con dati storici del benchmark o None se non disponibile
        """
        # Usa ticker come ISIN per cache
        cache_path = self._get_cache_path(benchmark_ticker, "benchmark")
        cached = self._load_cache(cache_path)
        if cached:
            try:
                from io import StringIO
                df = pd.read_json(StringIO(cached['data']), orient='records')
                # Ricostruisci DatetimeIndex
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                elif 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                else:
                    df.index = pd.date_range(start=datetime.now() - pd.Timedelta(days=len(df)), 
                                            periods=len(df), freq='D')
                
                # Rimuovi timezone se presente
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                
                return df
            except Exception as e:
                # Se cache è corrotta, continua a recuperare dati
                pass
        
        # Recupera dati da Yahoo Finance
        try:
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            # Usa _get_yahoo_data_smart per recuperare dati
            data = self._get_yahoo_data_smart(
                benchmark_ticker,
                start_date,
                end_date,
                is_us_mutual_fund=False
            )
            
            if data is not None and not data.empty:
                # Salva in cache (formato compatibile con _save_cache)
                # _save_cache si aspetta un dict, ma per DataFrame dobbiamo convertirlo
                cache_data = {
                    'data': data.to_json(orient='records', date_format='iso'),
                    'source': 'Yahoo Finance',
                    'validation': {'is_valid': True}
                }
                self._save_cache(cache_path, cache_data)
                return data
        except Exception as e:
            pass
        
        return None
    
    def _fetch_description_yahoo(self, ticker: str) -> Optional[str]:
        """
        Recupera descrizione dettagliata da Yahoo Finance
        
        Args:
            ticker: Ticker o identificatore Yahoo Finance
            
        Returns:
            Descrizione dettagliata (5-7 righe) o None se non disponibile
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Combina informazioni disponibili per creare descrizione professionale
            description_parts = []
            
            # Priorità 1: longBusinessSummary (descrizione completa)
            if 'longBusinessSummary' in info and info['longBusinessSummary']:
                summary = info['longBusinessSummary'].strip()
                # Limita a ~1000 caratteri per descrizione dettagliata (5-7 righe)
                if len(summary) > 1000:
                    # Cerca punto di interruzione naturale
                    truncated = summary[:1000]
                    last_period = truncated.rfind('.')
                    if last_period > 700:  # Se troviamo un punto dopo 700 caratteri
                        summary = summary[:last_period + 1]
                    else:
                        # Cerca spazio come alternativa
                        last_space = truncated.rfind(' ')
                        if last_space > 900:
                            summary = summary[:last_space] + '...'
                        else:
                            summary = truncated + '...'
                description_parts.append(summary)
            
            # Priorità 2: Se non c'è summary, costruisci da informazioni disponibili
            elif 'longName' in info or 'shortName' in info:
                name = info.get('longName') or info.get('shortName', '')
                
                if 'sector' in info and info['sector']:
                    description_parts.append(f"{name} opera nel settore {info['sector']}.")
                    if 'industry' in info and info['industry']:
                        description_parts.append(f"Industria: {info['industry']}.")
                
                if 'website' in info and info['website']:
                    description_parts.append(f"Sito web: {info['website']}.")
            
            # Priorità 3: Per ETF/indici, usa informazioni specifiche
            if 'category' in info and info['category']:
                if 'ETF' in info['category'] or 'Index' in info['category']:
                    description_parts.append(f"Categoria: {info['category']}.")
            
            if description_parts:
                description = ' '.join(description_parts)
                # Pulisci spazi multipli
                description = ' '.join(description.split())
                return description
                
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _fetch_description_wikipedia(self, name: str) -> Optional[str]:
        """
        Recupera descrizione da Wikipedia API come fallback
        
        Args:
            name: Nome della società, fondo o indice da cercare
            
        Returns:
            Descrizione (primo paragrafo, limitato a ~1000 caratteri) o None se non disponibile
        """
        try:
            import wikipedia
            wikipedia.set_lang("it")  # Prova prima in italiano
            
            # Cerca pagina Wikipedia con auto-suggest
            try:
                page = wikipedia.page(name, auto_suggest=True)
            except wikipedia.exceptions.DisambiguationError as e:
                # Se c'è ambiguità, usa la prima opzione
                page = wikipedia.page(e.options[0])
            except wikipedia.exceptions.PageError:
                # Prova in inglese se non trovato in italiano
                wikipedia.set_lang("en")
                try:
                    page = wikipedia.page(name, auto_suggest=True)
                except:
                    return None
            
            # Estrai summary (primo paragrafo)
            summary = page.summary.strip()
            
            # Limita a ~1000 caratteri (5-7 righe) cercando punto di interruzione naturale
            if len(summary) > 1000:
                truncated = summary[:1000]
                # Cerca ultimo punto prima di 1000 caratteri
                last_period = truncated.rfind('.')
                if last_period > 700:  # Se troviamo un punto dopo 700 caratteri
                    summary = summary[:last_period + 1]
                else:
                    # Cerca spazio come alternativa
                    last_space = truncated.rfind(' ')
                    if last_space > 900:
                        summary = summary[:last_space] + '...'
                    else:
                        summary = truncated + '...'
            
            return summary
            
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _fetch_description_morningstar(self, isin: str) -> Optional[str]:
        """
        Scraping descrizione da Morningstar per fondi
        
        Args:
            isin: ISIN del fondo
            
        Returns:
            Descrizione del fondo (strategia, obiettivi) o None se non disponibile
        """
        try:
            # URL Morningstar per la pagina del fondo
            url = f"https://www.morningstar.it/it/funds/snapshot/snapshot.aspx?id={isin}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.morningstar.it/'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Verifica se il fondo esiste
                title = soup.find('title')
                if title and ('not found' in title.text.lower() or 'errore' in title.text.lower()):
                    return None
                
                description_parts = []
                
                # Cerca sezione descrizione/strategia
                # Morningstar spesso ha una sezione "Strategia" o "Descrizione"
                strategy_section = soup.find('div', class_=lambda x: x and ('strategy' in x.lower() or 'description' in x.lower() or 'overview' in x.lower()))
                if not strategy_section:
                    # Prova a cercare in altre sezioni comuni
                    strategy_section = soup.find('section', class_=lambda x: x and ('strategy' in x.lower() or 'description' in x.lower()))
                
                if strategy_section:
                    # Estrai testo dalla sezione
                    text = strategy_section.get_text(separator=' ', strip=True)
                    if text and len(text) > 50:  # Almeno 50 caratteri per essere significativo
                        # Limita a ~1000 caratteri (5-7 righe)
                        if len(text) > 1000:
                            truncated = text[:1000]
                            last_period = truncated.rfind('.')
                            if last_period > 700:
                                text = text[:last_period + 1]
                            else:
                                # Cerca spazio come alternativa
                                last_space = truncated.rfind(' ')
                                if last_space > 900:
                                    text = text[:last_space] + '...'
                                else:
                                    text = truncated + '...'
                        description_parts.append(text)
                
                # Cerca anche informazioni su obiettivi di investimento
                objective_section = soup.find('div', class_=lambda x: x and 'objective' in x.lower())
                if objective_section:
                    objective_text = objective_section.get_text(separator=' ', strip=True)
                    if objective_text and len(objective_text) > 30:
                        if len(description_parts) == 0 or len(description_parts[0]) < 300:
                            # Aggiungi obiettivi se la descrizione è breve
                            if len(objective_text) > 200:
                                objective_text = objective_text[:200] + '...'
                            description_parts.append(f"Obiettivi: {objective_text}")
                
                if description_parts:
                    description = ' '.join(description_parts)
                    # Pulisci spazi multipli
                    description = ' '.join(description.split())
                    return description
                    
        except Exception as e:
            # Silently fail, useremo altre fonti
            pass
        
        return None
    
    def _fetch_description_alpha_vantage(self, symbol: str) -> Optional[str]:
        """
        Recupera descrizione da Alpha Vantage API (se disponibile)
        
        Args:
            symbol: Simbolo del titolo
            
        Returns:
            Descrizione o None se non disponibile
        """
        if not config.ALPHA_VANTAGE_API_KEY:
            return None
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': config.ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Description' in data and data['Description']:
                    description = data['Description'].strip()
                    # Limita a ~1000 caratteri (5-7 righe)
                    if len(description) > 1000:
                        truncated = description[:1000]
                        last_period = truncated.rfind('.')
                        if last_period > 700:
                            description = description[:last_period + 1]
                        else:
                            # Cerca spazio come alternativa
                            last_space = truncated.rfind(' ')
                            if last_space > 900:
                                description = description[:last_space] + '...'
                            else:
                                description = truncated + '...'
                    return description
        except:
            pass
        
        return None
    
    def _fetch_description_fmp(self, symbol: str) -> Optional[str]:
        """
        Recupera descrizione da Financial Modeling Prep API (se disponibile)
        
        Args:
            symbol: Simbolo del titolo
            
        Returns:
            Descrizione o None se non disponibile
        """
        if not config.FMP_API_KEY:
            return None
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
            params = {'apikey': config.FMP_API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    profile = data[0]
                    if 'description' in profile and profile['description']:
                        description = profile['description'].strip()
                        # Limita a ~1000 caratteri (5-7 righe)
                        if len(description) > 1000:
                            truncated = description[:1000]
                            last_period = truncated.rfind('.')
                            if last_period > 700:
                                description = description[:last_period + 1]
                            else:
                                # Cerca spazio come alternativa
                                last_space = truncated.rfind(' ')
                                if last_space > 900:
                                    description = description[:last_space] + '...'
                                else:
                                    description = truncated + '...'
                        return description
        except:
            pass
        
        return None
    
    def _fetch_detailed_description(self, isin: str, ticker: Optional[str] = None, 
                                    name: Optional[str] = None) -> Tuple[Optional[str], str]:
        """
        Recupera descrizione dettagliata da multiple fonti con fallback automatico
        
        Ordine di priorità:
        1. Yahoo Finance (più affidabile per dati finanziari)
        2. Alpha Vantage (se API key disponibile)
        3. Financial Modeling Prep (se API key disponibile)
        4. Wikipedia (ampia copertura)
        5. Morningstar scraping (per fondi)
        
        Args:
            isin: ISIN del fondo/titolo
            ticker: Ticker Yahoo Finance (opzionale, verrà cercato se non fornito)
            name: Nome del fondo/titolo (opzionale, per ricerca Wikipedia)
            
        Returns:
            Tupla (descrizione, fonte_utilizzata) o (None, '') se non disponibile
        """
        # Prova Yahoo Finance per primo
        if ticker:
            description = self._fetch_description_yahoo(ticker)
            if description:
                return description, 'Yahoo Finance'
        
        # Se non abbiamo ticker, prova a ottenerlo
        if not ticker:
            ticker = self._isin_to_ticker(isin)
            if ticker:
                description = self._fetch_description_yahoo(ticker)
                if description:
                    return description, 'Yahoo Finance'
        
        # Prova Alpha Vantage se API key disponibile
        if ticker:
            description = self._fetch_description_alpha_vantage(ticker)
            if description:
                return description, 'Alpha Vantage'
        
        # Prova Financial Modeling Prep se API key disponibile
        if ticker:
            description = self._fetch_description_fmp(ticker)
            if description:
                return description, 'Financial Modeling Prep'
        
        # Prova Wikipedia (usa nome se disponibile, altrimenti ticker o ISIN)
        search_name = name
        if not search_name and ticker:
            search_name = ticker
        if not search_name:
            search_name = isin
        
        if search_name:
            description = self._fetch_description_wikipedia(search_name)
            if description:
                return description, 'Wikipedia'
        
        # Prova Morningstar scraping (soprattutto per fondi)
        description = self._fetch_description_morningstar(isin)
        if description:
            return description, 'Morningstar'
        
        # Nessuna descrizione trovata
        return None, ''
    
    def get_fund_description(self, isin: str, ticker: Optional[str] = None, 
                             name: Optional[str] = None) -> Tuple[Optional[str], str]:
        """
        Recupera descrizione dettagliata del fondo con caching
        
        Args:
            isin: ISIN del fondo/titolo
            ticker: Ticker Yahoo Finance (opzionale)
            name: Nome del fondo/titolo (opzionale)
            
        Returns:
            Tupla (descrizione, fonte_utilizzata) o (None, '') se non disponibile
        """
        # Prova a caricare dalla cache
        cached = self._load_description_cache(isin)
        if cached:
            return cached
        
        # Recupera descrizione da multiple fonti
        description, source = self._fetch_detailed_description(isin, ticker, name)
        
        # Salva in cache se trovata
        if description:
            self._save_description_cache(isin, description, source)
        
        return description, source
    
    def _scrape_justetf(self, isin: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Scraping dati storici da JustETF (utile per ETF e alcuni fondi)
        """
        try:
            url = f"https://www.justetf.com/it/etf-profile.html?isin={isin}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                # JustETF ha principalmente ETF, ma alcuni fondi potrebbero essere presenti
                # Richiede parsing specifico
                return None
        except Exception as e:
            pass
        
        return None
    
    def get_fund_composition(self, isin: str) -> Dict:
        """
        Recupera composizione del fondo (settori e top holdings)
        """
        cache_path = self._get_cache_path(isin, "composition")
        cached = self._load_cache(cache_path)
        if cached:
            return cached
        
        composition = {
            'sectors': {},
            'top_holdings': [],
            'geographic_allocation': {},
            'data_source': None
        }
        
        # Prova a recuperare da Yahoo Finance
        ticker = self._isin_to_ticker(isin)
        if ticker:
            yahoo_info = self._get_fund_info_from_yahoo(ticker)
            if yahoo_info.get('sectors') or yahoo_info.get('top_holdings'):
                composition.update(yahoo_info)
                composition['data_source'] = 'Yahoo Finance'
        
        # Web scraping da Morningstar come fallback (solo se non abbiamo dati)
        if not composition['sectors'] and not composition['top_holdings']:
            scraped = self._scrape_fund_composition(isin)
            if scraped and (scraped.get('sectors') or scraped.get('top_holdings')):
                composition.update(scraped)
                if not composition['data_source']:
                    composition['data_source'] = 'Morningstar'
        
        # Rimuovi error se non c'è
        if 'error' in composition and composition['error'] is None:
            del composition['error']
        
        # Salva in cache
        self._save_cache(cache_path, composition)
        
        return composition
    
    def _scrape_fund_composition(self, isin: str) -> Optional[Dict]:
        """
        Web scraping per composizione fondo da Morningstar o altre fonti
        """
        try:
            # URL Morningstar per ISIN
            url = f"https://www.morningstar.it/it/funds/snapshot/snapshot.aspx?id={isin}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Estrai dati di composizione (struttura dipende dal sito)
                # Questo è un template - va adattato alla struttura HTML reale
                composition = {
                    'sectors': {},
                    'top_holdings': []
                }
                
                # Cerca tabelle con settori
                sector_tables = soup.find_all('table', class_=lambda x: x and 'sector' in x.lower())
                # ... logica di estrazione ...
                
                return composition if composition['sectors'] or composition['top_holdings'] else None
                
        except Exception as e:
            print(f"Errore nello scraping per {isin}: {e}")
        
        return None
    
    def analyze_single_fund(self, isin: str, years: int = 5) -> Dict:
        """
        Analizza un singolo fondo per ISIN (senza bisogno di config)
        
        Args:
            isin: Codice ISIN del fondo
            years: Numero di anni di dati storici da recuperare
        
        Returns:
            Dict con dati completi del fondo
        """
        print(f"Analisi fondo ISIN: {isin}")
        
        # Fetch metadati da Open FIGI se disponibile
        figi_metadata = self._get_figi_metadata(isin)
        fund_name = figi_metadata.get('name', f'Fondo {isin}')
        
        if figi_metadata:
            print(f"  Nome trovato: {fund_name}")
        
        # Dati storici
        historical = self.get_historical_data(isin, years)
        
        # Composizione
        composition = self.get_fund_composition(isin)
        
        return {
            'isin': isin,
            'name': fund_name,
            'name_short': fund_name[:50] if len(fund_name) > 50 else fund_name,
            'metadata': figi_metadata,
            'historical_data': historical,
            'composition': composition
        }
    
    def collect_all_funds_data(self, funds_config: Optional[Dict] = None) -> Dict:
        """
        Raccoglie dati per tutti i fondi configurati
        Se funds_config è None, usa config.load_funds_config()
        
        Args:
            funds_config: Dict opzionale con configurazione fondi
        
        Returns:
            Dict con dati di tutti i fondi
        """
        if funds_config is None:
            funds_config = config.load_funds_config()
        
        all_data = {}
        
        for fund_name, fund_info in funds_config.items():
            # Supporta sia 'isin' che 'ISIN' come chiave
            isin = fund_info.get('isin') or fund_info.get('ISIN')
            if not isin:
                print(f"  ⚠ Fondo {fund_name} senza ISIN, skip")
                continue
            
            print(f"Raccolta dati per {fund_name} ({isin})...")
            
            # Dati storici
            historical = self.get_historical_data(isin, config.YEARS_BACK)
            
            # Composizione
            composition = self.get_fund_composition(isin)
            
            # Descrizione dettagliata
            description, description_source = self.get_fund_description(
                isin, 
                ticker=fund_info.get('ticker'),
                name=fund_info.get('name_short') or fund_name
            )
            
            all_data[fund_name] = {
                'isin': isin,
                'name_short': fund_info.get('name_short', fund_name),
                'historical_data': historical,
                'composition': composition,
                'description': description,
                'description_source': description_source
            }
            
            # Pausa per evitare rate limiting
            time.sleep(1)
        
        return all_data
