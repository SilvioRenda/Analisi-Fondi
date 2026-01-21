"""
Modulo per l'elaborazione e normalizzazione dei dati
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import config


class DataProcessor:
    """Elabora e normalizza i dati dei fondi"""
    
    def __init__(self):
        self.base_value = config.BASE_VALUE
        # Inizializza sector classifier se disponibile
        self.sector_classifier = None
        self.advanced_metrics_calc = None
        try:
            from lib_manager import LibraryManager
            lib_manager = LibraryManager()
            self.sector_classifier = lib_manager.get_sector_classifier()
            self.advanced_metrics_calc = lib_manager.get_metric_calculator()
        except Exception:
            pass  # Fallback a classificazione manuale
    
    def _determine_benchmark(self, isin: str, ticker: Optional[str] = None) -> tuple[str, str]:
        """
        Determina benchmark appropriato in base alla geografia del titolo/fondo
        
        Args:
            isin: ISIN del titolo/fondo
            ticker: Ticker del titolo/fondo (opzionale)
            
        Returns:
            Tupla (benchmark_ticker, benchmark_name)
            - Per US: ('SPY', 'S&P 500')
            - Per Europei: ('EZU', 'Euro Stoxx 50')
            - Default: ('SPY', 'S&P 500')
        """
        # Codici paese europei comuni
        european_countries = ['LU', 'IE', 'FR', 'DE', 'IT', 'ES', 'NL', 'GB', 'BE', 'AT', 'CH', 'SE', 'NO', 'DK', 'FI']
        
        # Determina se è US o Europeo
        if isin:
            isin_prefix = isin[:2]  # Primi 2 caratteri del codice paese
            
            if isin_prefix == 'US':
                return ('SPY', 'S&P 500')
            elif isin_prefix in european_countries:
                return ('EZU', 'Euro Stoxx 50')
        
        # Fallback: se ticker è noto e sembra US (es. AAPL, MSFT)
        if ticker and len(ticker) <= 5 and ticker.isalpha():
            # Ticker corti sono tipicamente US
            return ('SPY', 'S&P 500')
        
        # Default a S&P 500
        return ('SPY', 'S&P 500')
    
    def calculate_total_return(self, data: pd.DataFrame, 
                              price_column: str = 'Price',
                              dividends_column: str = 'Dividends',
                              capital_gains_column: str = 'Capital Gains') -> pd.Series:
        """
        Calcola Total Return includendo dividendi e capital gains reinvestiti
        
        IMPORTANTE: Se i prezzi sono già adjusted (colonna _is_adjusted = True), 
        NON aggiunge dividendi perché sono già inclusi nel prezzo.
        
        Formula per prezzi unadjusted:
        Cumulative Total Return = Price_0 * prod((Price_t + Dividend_t + CapitalGain_t) / Price_{t-1})
        
        Formula per prezzi adjusted:
        Cumulative Total Return = Price_0 * prod(Price_t / Price_{t-1})
        (i prezzi adjusted già includono dividendi reinvestiti)
        
        Args:
            data: DataFrame con colonne Price, Dividends e opzionalmente Capital Gains
            price_column: Nome colonna prezzo
            dividends_column: Nome colonna dividendi
            capital_gains_column: Nome colonna capital gains
            
        Returns:
            Serie pandas con Total Return cumulativo
        """
        if data is None or data.empty:
            return pd.Series(dtype=float)
        
        prices = data[price_column].copy()
        
        # Verifica se i prezzi sono già adjusted
        is_adjusted = data.get('_is_adjusted', False) if hasattr(data, 'get') else False
        if '_is_adjusted' in data.columns:
            # Se la colonna esiste, usa il primo valore (dovrebbero essere tutti uguali)
            is_adjusted = data['_is_adjusted'].iloc[0] if len(data) > 0 else False
        
        # Se i prezzi sono già adjusted, usa direttamente i prezzi senza aggiungere dividendi
        if is_adjusted:
            # Prezzi adjusted già includono dividendi reinvestiti
            # Calcola semplicemente il return cumulativo basato sui prezzi
            if len(prices) == 0:
                return pd.Series(dtype=float)
            
            total_return = pd.Series(index=prices.index, dtype=float)
            total_return.iloc[0] = prices.iloc[0]
            
            for i in range(1, len(prices)):
                prev_price = prices.iloc[i-1]
                curr_price = prices.iloc[i]
                
                if pd.notna(prev_price) and prev_price != 0 and pd.notna(curr_price):
                    daily_return = curr_price / prev_price
                    total_return.iloc[i] = total_return.iloc[i-1] * daily_return
                else:
                    total_return.iloc[i] = total_return.iloc[i-1] if i > 0 else curr_price
            
            # Validazione: Total Return >= Price Return sempre
            if len(total_return) > 1 and len(prices) > 1:
                price_return = prices.iloc[-1] / prices.iloc[0]
                total_return_final = total_return.iloc[-1] / total_return.iloc[0]
                if total_return_final < price_return:
                    import warnings
                    warnings.warn(
                        f"ATTENZIONE: Total Return ({total_return_final:.4f}) < Price Return ({price_return:.4f}). "
                        "Questo non dovrebbe accadere se il calcolo è corretto."
                    )
            
            return total_return
        
        # Prezzi unadjusted: aggiungi dividendi e capital gains
        # Recupera dividendi e capital gains, default a 0 se non presenti
        if dividends_column in data.columns:
            dividends = data[dividends_column].fillna(0)
        else:
            dividends = pd.Series(0.0, index=prices.index)
        
        if capital_gains_column in data.columns:
            capital_gains = data[capital_gains_column].fillna(0)
        else:
            capital_gains = pd.Series(0.0, index=prices.index)
        
        # Combina tutte le distribuzioni
        distributions = dividends + capital_gains
        
        # Calcola Total Return cumulativo
        # Inizia con il primo prezzo
        if len(prices) == 0:
            return pd.Series(dtype=float)
        
        total_return = pd.Series(index=prices.index, dtype=float)
        total_return.iloc[0] = prices.iloc[0]
        
        # Per ogni giorno successivo, calcola il Total Return
        # Per fondi comuni: quando distribuiscono, il prezzo si abbassa (ex-dividend)
        # Il prezzo corrente è già ex-dividend, quindi dobbiamo aggiungere la distribuzione
        # per ottenere il valore totale (prezzo + distribuzione reinvestita)
        for i in range(1, len(prices)):
            prev_price = prices.iloc[i-1]
            curr_price = prices.iloc[i]
            distribution = distributions.iloc[i]
            
            if pd.notna(prev_price) and prev_price != 0 and pd.notna(curr_price):
                # Formula corretta per Total Return:
                # Il prezzo corrente è già ex-dividend (si è abbassato della distribuzione)
                # Per calcolare il Total Return, dobbiamo considerare:
                # - Il prezzo ex-dividend corrente
                # - La distribuzione che è stata pagata e reinvestita
                # Return = (prezzo_ex_dividend + distribuzione) / prezzo_precedente
                # Ma il prezzo corrente è già ex-dividend, quindi:
                if distribution > 0:
                    # C'è una distribuzione: il prezzo si è abbassato, aggiungiamo la distribuzione
                    # per ottenere il valore totale con reinvestimento
                    total_value = curr_price + distribution
                else:
                    # Nessuna distribuzione: solo variazione prezzo
                    total_value = curr_price
                
                daily_return = total_value / prev_price
                # Cumulative Total Return
                total_return.iloc[i] = total_return.iloc[i-1] * daily_return
            else:
                total_return.iloc[i] = total_return.iloc[i-1] if i > 0 else curr_price
        
        # Validazione: Total Return >= Price Return sempre
        # Se ci sono distribuzioni (dividendi o capital gains), Total Return dovrebbe essere >= Price Return
        if len(total_return) > 1 and len(prices) > 1:
            price_return_ratio = prices.iloc[-1] / prices.iloc[0]
            total_return_ratio = total_return.iloc[-1] / total_return.iloc[0]
            if total_return_ratio < price_return_ratio:
                import warnings
                warnings.warn(
                    f"ATTENZIONE: Total Return ({total_return_ratio:.4f}) < Price Return ({price_return_ratio:.4f}). "
                    "Questo non dovrebbe accadere se il calcolo è corretto. Verificare dati o formula."
                )
        
        return total_return
    
    def normalize_to_base100(self, data: pd.DataFrame, 
                             price_column: str = 'Price',
                             use_total_return: bool = True) -> pd.DataFrame:
        """
        Normalizza i dati in base 100
        Il primo valore diventa 100, tutti gli altri sono relativi a quello
        
        IMPORTANTE - Adjusted vs Unadjusted:
        - Se data contiene colonna '_is_adjusted = True': i prezzi già includono dividendi reinvestiti
          (da EOD, Alpha Vantage, FMP). In questo caso, use_total_return calcola solo price return.
        - Se data contiene colonna '_is_adjusted = False': i prezzi sono unadjusted (da Yahoo Finance).
          In questo caso, use_total_return calcola Total Return aggiungendo dividendi.
        
        Formula normalizzazione:
        normalized_value = (value / first_value) * 100
        
        Args:
            data: DataFrame con dati storici (deve contenere Price e opzionalmente Dividends)
            price_column: Nome colonna prezzo
            use_total_return: Se True, calcola Total Return includendo dividendi prima di normalizzare
                              (solo se prezzi sono unadjusted, altrimenti usa direttamente i prezzi adjusted)
        """
        if data is None or data.empty:
            return pd.DataFrame()
        
        # Assicurati che ci sia un indice DatetimeIndex per la normalizzazione corretta
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data = data.set_index('Date')
            elif 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data = data.set_index('date')
            else:
                # Fallback: crea un indice di date approssimativo se non esiste
                # (non ideale, ma necessario per cache vecchie senza colonna Date)
                data.index = pd.date_range(start=datetime.now() - pd.Timedelta(days=len(data)), 
                                          periods=len(data), freq='D')
        
        # Ordina per data
        data = data.sort_index()
        
        # Calcola Total Return se richiesto e se ci sono distribuzioni
        if use_total_return and ('Dividends' in data.columns or 'Capital Gains' in data.columns):
            values = self.calculate_total_return(data, price_column, 'Dividends', 'Capital Gains')
        else:
            # Usa solo il prezzo
            if price_column not in data.columns:
                # Se non c'è, prova con la prima colonna numerica
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    price_column = numeric_cols[0]
                else:
                    return pd.DataFrame()
            values = data[price_column].copy()
        
        # Rimuovi valori nulli
        values = values.dropna()
        
        if len(values) == 0:
            return pd.DataFrame()
        
        # Normalizza: primo valore = BASE_VALUE
        first_value = values.iloc[0]
        if first_value == 0:
            return pd.DataFrame()
        
        normalized = (values / first_value) * self.base_value
        
        # Crea DataFrame risultato
        result = pd.DataFrame({
            'Date': normalized.index,
            'Normalized_Value': normalized.values
        })
        result = result.set_index('Date')
        
        return result
    
    def calculate_metrics(self, normalized_data: pd.DataFrame) -> Dict:
        """
        Calcola metriche di performance
        
        Metriche calcolate:
        - Total Return: ((valore_finale - valore_iniziale) / valore_iniziale) * 100
        - Return Annualizzato: ((valore_finale / valore_iniziale) ^ (1 / years) - 1) * 100
          dove years = giorni_totali / 365.25
        - Volatilità: std(returns_giornalieri) * sqrt(252) * 100
          - returns_giornalieri in forma decimale (0.05 per 5%)
          - sqrt(252) annualizza usando 252 giorni lavorativi all'anno
          - * 100 converte da decimale a percentuale
        - Sharpe Ratio: annualized_return / volatility (assumendo risk-free rate = 0)
        - Max Drawdown: minimo drawdown percentuale durante il periodo
        
        Convenzioni:
        - Returns in forma decimale (0.05 = 5%)
        - Volatilità annualizzata con 252 giorni lavorativi (standard per azioni/ETF)
        - Anno = 365.25 giorni (include anni bisestili)
        """
        if normalized_data is None or normalized_data.empty:
            return {
                'total_return': None,
                'annualized_return': None,
                'volatility': None,
                'sharpe_ratio': None,
                'max_drawdown': None
            }
        
        values = normalized_data['Normalized_Value'].values
        
        # Return totale
        if len(values) > 0:
            total_return = ((values[-1] - values[0]) / values[0]) * 100
        else:
            total_return = None
        
        # Return annualizzato
        if len(values) > 1:
            days = (normalized_data.index[-1] - normalized_data.index[0]).days
            years = days / 365.25
            if years > 0:
                annualized_return = ((values[-1] / values[0]) ** (1 / years) - 1) * 100
            else:
                annualized_return = None
        else:
            annualized_return = None
        
        # Volatilità (deviazione standard dei returns giornalieri annualizzata)
        # Formula: std(returns_giornalieri) * sqrt(252) * 100
        # - returns_giornalieri = np.diff(values) / values[:-1] restituisce decimali (es: 0.05 per 5%)
        # - np.std(returns) calcola deviazione standard in forma decimale
        # - sqrt(252) annualizza (252 giorni lavorativi all'anno)
        # - * 100 converte da decimale a percentuale
        if len(values) > 1:
            # Calcola returns giornalieri in forma decimale (es: 0.05 per 5%)
            returns = np.diff(values) / values[:-1]
            # Annualizza e converte in percentuale
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualizzata in %
        else:
            volatility = None
        
        # Sharpe Ratio (assumendo risk-free rate = 0 per semplicità)
        if annualized_return is not None and volatility is not None and volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = None
        
        # Max Drawdown
        if len(values) > 0:
            cumulative_max = np.maximum.accumulate(values)
            drawdown = (values - cumulative_max) / cumulative_max * 100
            max_drawdown = drawdown.min()
        else:
            max_drawdown = None
        
        metrics = {
            'total_return': round(total_return, 2) if total_return is not None else None,
            'annualized_return': round(annualized_return, 2) if annualized_return is not None else None,
            'volatility': round(volatility, 2) if volatility is not None else None,
            'sharpe_ratio': round(sharpe_ratio, 2) if sharpe_ratio is not None else None,
            'max_drawdown': round(max_drawdown, 2) if max_drawdown is not None else None
        }
        
        # Aggiungi metriche avanzate se disponibili
        if self.advanced_metrics_calc and len(values) > 1:
            try:
                # Calcola returns per metriche avanzate
                returns = pd.Series(np.diff(values) / values[:-1], index=normalized_data.index[1:])
                
                # Calcola metriche avanzate
                advanced = self.advanced_metrics_calc.calculate_from_data(returns)
                
                # Aggiungi metriche avanzate se disponibili
                if advanced.get('sortino_ratio') is not None:
                    metrics['sortino_ratio'] = round(advanced['sortino_ratio'], 2)
                if advanced.get('alpha') is not None:
                    metrics['alpha'] = round(advanced['alpha'], 2)
            except Exception:
                pass  # Continua senza metriche avanzate
        
        return metrics
    
    def calculate_beta(self, fund_prices: pd.Series, benchmark_prices: pd.Series) -> Optional[float]:
        """
        Calcola Beta del fondo rispetto al benchmark
        
        Formula: Beta = Covariance(fund_returns, benchmark_returns) / Variance(benchmark_returns)
        
        Args:
            fund_prices: Serie con prezzi del fondo (normalizzati o assoluti)
            benchmark_prices: Serie con prezzi del benchmark (normalizzati o assoluti)
            
        Returns:
            Beta (float) o None se dati insufficienti
        """
        if fund_prices is None or benchmark_prices is None:
            return None
        
        if fund_prices.empty or benchmark_prices.empty:
            return None
        
        try:
            # Allinea serie temporali (stesse date)
            aligned_fund, aligned_benchmark = fund_prices.align(benchmark_prices, join='inner')
            
            if len(aligned_fund) < 30:  # Minimo 30 giorni per calcolo Beta affidabile
                return None
            
            # Calcola returns giornalieri (percentuale di variazione)
            fund_returns = aligned_fund.pct_change().dropna()
            benchmark_returns = aligned_benchmark.pct_change().dropna()
            
            # Allinea di nuovo dopo pct_change (potrebbero esserci NaN)
            fund_returns, benchmark_returns = fund_returns.align(benchmark_returns, join='inner')
            
            if len(fund_returns) < 30:  # Verifica dopo allineamento
                return None
            
            # Calcola covarianza e varianza
            covariance = fund_returns.cov(benchmark_returns)
            variance = benchmark_returns.var()
            
            if variance > 0 and not np.isnan(covariance) and not np.isnan(variance):
                beta = covariance / variance
                return round(beta, 2) if not np.isnan(beta) else None
            else:
                return None
                
        except Exception as e:
            # In caso di errore, ritorna None
            return None
    
    def _determine_sector(self, fund_data: Dict) -> Optional[str]:
        """
        Determina il settore di un fondo/titolo da multiple fonti
        
        Priorità:
        1. FinanceDatabase (se disponibile)
        2. config.FUNDS (campo category)
        3. Analisi nome/ticker (fallback)
        
        Args:
            fund_data: Dizionario con dati del fondo
            
        Returns:
            Nome del settore o None se non determinabile
        """
        import config
        
        # Fonte 1: FinanceDatabase (se disponibile)
        if self.sector_classifier:
            try:
                ticker = fund_data.get('ticker')
                isin = fund_data.get('isin')
                sector = self.sector_classifier.classify_fund(fund_data, ticker=ticker, isin=isin)
                if sector:
                    return sector
            except Exception:
                pass  # Fallback a metodi manuali
        
        # Fonte 2: Da config.FUNDS (campo category)
        fund_name = fund_data.get('name_short', '')
        fund_info = config.FUNDS.get(fund_name, {})
        if not fund_info:
            # Prova a cercare per nome completo
            for key, value in config.FUNDS.items():
                if value.get('name_short') == fund_name:
                    fund_info = value
                    break
        
        if fund_info:
            category = fund_info.get('category', '')
            if category:
                # Estrai settore da categoria (es. "Azionario - Healthcare" -> "Healthcare")
                if ' - ' in category:
                    sector = category.split(' - ')[-1]
                    return sector
                elif 'Healthcare' in category or 'Health' in category:
                    return 'Healthcare'
                elif 'Technology' in category or 'Tech' in category:
                    return 'Technology'
                elif 'Finance' in category or 'Financial' in category:
                    return 'Finance'
        
        # Fonte 2: Analisi nome/ticker
        name_lower = fund_name.lower()
        if any(word in name_lower for word in ['health', 'healthcare', 'medical', 'pharma', 'biotech']):
            return 'Healthcare'
        elif any(word in name_lower for word in ['tech', 'technology', 'software', 'digital']):
            return 'Technology'
        elif any(word in name_lower for word in ['finance', 'financial', 'bank', 'insurance']):
            return 'Finance'
        elif any(word in name_lower for word in ['energy', 'oil', 'gas']):
            return 'Energy'
        elif any(word in name_lower for word in ['consumer', 'retail']):
            return 'Consumer'
        
        # Fallback: usa categoria generica se disponibile
        if fund_info and fund_info.get('category'):
            return fund_info.get('category')
        
        return None
    
    def group_by_sector(self, processed_data: Dict) -> Dict[str, List[str]]:
        """
        Raggruppa fondi per settore
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            
        Returns:
            Dict con struttura: {sector: [fund_name1, fund_name2, ...]}
        """
        sectors = {}
        
        for fund_name, fund_data in processed_data.items():
            # Determina settore
            sector = self._determine_sector(fund_data)
            
            if sector:
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(fund_name)
            else:
                # Se settore non determinabile, usa "Altro"
                if 'Altro' not in sectors:
                    sectors['Altro'] = []
                sectors['Altro'].append(fund_name)
        
        # Filtra settori con almeno 2 fondi (per confronto)
        return {sector: funds for sector, funds in sectors.items() if len(funds) >= 2}
    
    def process_all_funds(self, funds_data: Dict, collector=None) -> Dict:
        """
        Elabora dati per tutti i fondi
        
        Args:
            funds_data: Dizionario con dati dei fondi
            collector: DataCollector opzionale per recuperare dati benchmark (per calcolo Beta)
        """
        processed_data = {}
        
        # Cache per dati benchmark (evita recuperi multipli)
        benchmark_cache = {}
        
        for fund_name, fund_data in funds_data.items():
            historical = fund_data.get('historical_data')
            
            if historical is not None and not historical.empty:
                # Normalizza
                normalized = self.normalize_to_base100(historical)
                
                # Calcola metriche base
                metrics = self.calculate_metrics(normalized)
                
                # Calcola Beta se collector disponibile
                beta = None
                benchmark_name = None
                if collector is not None:
                    isin = fund_data.get('isin', '')
                    ticker = fund_data.get('ticker')
                    
                    # Determina benchmark appropriato
                    benchmark_ticker, benchmark_name = self._determine_benchmark(isin, ticker)
                    
                    # Recupera dati benchmark (usa cache se disponibile)
                    if benchmark_ticker not in benchmark_cache:
                        benchmark_data = collector.get_benchmark_data(benchmark_ticker, config.YEARS_BACK)
                        if benchmark_data is not None and not benchmark_data.empty:
                            benchmark_cache[benchmark_ticker] = benchmark_data
                        else:
                            benchmark_cache[benchmark_ticker] = None
                    
                    benchmark_data = benchmark_cache[benchmark_ticker]
                    
                    if benchmark_data is not None and not benchmark_data.empty:
                        # Prepara serie prezzi per calcolo Beta
                        # Usa colonna Price se disponibile, altrimenti Close
                        if 'Price' in benchmark_data.columns:
                            benchmark_prices = benchmark_data['Price']
                        elif 'Close' in benchmark_data.columns:
                            benchmark_prices = benchmark_data['Close']
                        elif 'Adj Close' in benchmark_data.columns:
                            benchmark_prices = benchmark_data['Adj Close']
                        else:
                            benchmark_prices = benchmark_data.iloc[:, 0]  # Prima colonna numerica
                        
                        # Prepara serie prezzi fondo
                        if 'Price' in historical.columns:
                            fund_prices = historical['Price']
                        elif 'Close' in historical.columns:
                            fund_prices = historical['Close']
                        elif 'Adj Close' in historical.columns:
                            fund_prices = historical['Adj Close']
                        else:
                            fund_prices = historical.iloc[:, 0]  # Prima colonna numerica
                        
                        # Calcola Beta (prova prima con advanced metrics, poi fallback manuale)
                        beta = None
                        if self.advanced_metrics_calc:
                            try:
                                ticker = fund_data.get('ticker', '')
                                if not ticker:
                                    # Prova a estrarre ticker da ISIN o nome
                                    ticker = fund_data.get('isin', fund_name)
                                
                                beta_result = self.advanced_metrics_calc.calculate_beta_advanced(
                                    ticker, benchmark_ticker
                                )
                                if beta_result and beta_result.get('beta') is not None:
                                    beta = beta_result['beta']
                            except Exception:
                                pass  # Fallback a calcolo manuale
                        
                        # Fallback: calcolo Beta manuale
                        if beta is None:
                            beta = self.calculate_beta(fund_prices, benchmark_prices)
                
                # Aggiungi Beta alle metriche
                if beta is not None:
                    metrics['beta'] = beta
                    metrics['benchmark'] = benchmark_name
                
                processed_data[fund_name] = {
                    'isin': fund_data['isin'],
                    'name_short': fund_data['name_short'],
                    'normalized_data': normalized,
                    'metrics': metrics,
                    'composition': fund_data.get('composition', {}),
                    'description': fund_data.get('description'),
                    'description_source': fund_data.get('description_source', '')
                }
            else:
                # Fondo senza dati storici
                processed_data[fund_name] = {
                    'isin': fund_data['isin'],
                    'name_short': fund_data['name_short'],
                    'normalized_data': pd.DataFrame(),
                    'metrics': {},
                    'composition': fund_data.get('composition', {}),
                    'description': fund_data.get('description'),
                    'description_source': fund_data.get('description_source', ''),
                    'error': 'Dati storici non disponibili'
                }
        
        return processed_data
    
    def create_comparison_dataframe(self, processed_data: Dict, 
                                    custom_start_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Crea un DataFrame unificato con tutte le serie normalizzate per il grafico
        Assicura che tutti i fondi partano da 100 alla stessa data iniziale
        
        Args:
            processed_data: Dati processati dei fondi
            custom_start_date: Data di inizio personalizzata (opzionale). 
                              Se None, usa la data comune automatica (più recente)
        """
        all_series = []
        start_dates = []
        
        # Raccogli tutte le serie e trova la data di inizio comune
        for fund_name, fund_data in processed_data.items():
            normalized = fund_data.get('normalized_data')
            if normalized is not None and not normalized.empty:
                series = normalized['Normalized_Value'].copy()
                # Normalizza timezone: rimuovi timezone per evitare errori di confronto
                if series.index.tz is not None:
                    series.index = series.index.tz_localize(None)
                series.name = fund_data['name_short']
                all_series.append(series)
                start_dates.append(series.index[0])
        
        if not all_series:
            return pd.DataFrame()
        
        # Usa data personalizzata se specificata, altrimenti trova la data comune
        if custom_start_date is not None:
            # Converti custom_start_date a datetime se è stringa
            if isinstance(custom_start_date, str):
                from pandas import to_datetime
                custom_start_date = to_datetime(custom_start_date)
            # Normalizza timezone
            if hasattr(custom_start_date, 'tz') and custom_start_date.tz is not None:
                custom_start_date = custom_start_date.tz_localize(None)
            common_start_date = custom_start_date
        else:
            # Trova la data di inizio comune (la più recente tra tutte)
            # Normalizza tutte le date per rimuovere timezone prima del confronto
            start_dates_normalized = [d.tz_localize(None) if hasattr(d, 'tz') and d.tz is not None else d for d in start_dates]
            common_start_date = max(start_dates_normalized)
        
        # Combina tutte le serie in un DataFrame
        comparison_df = pd.concat(all_series, axis=1)
        
        # Filtra per iniziare dalla data comune
        comparison_df = comparison_df[comparison_df.index >= common_start_date]
        
        # Per ogni colonna, ri-normalizza per partire da 100 alla data comune
        for col in comparison_df.columns:
            # Trova il primo valore non-null per questa colonna
            col_data = comparison_df[col].dropna()
            if len(col_data) > 0:
                first_valid_idx = col_data.index[0]
                first_valid_value = col_data.iloc[0]
                
                # Se il primo valore valido è alla data comune o dopo
                if first_valid_idx >= common_start_date and first_valid_value != 0 and pd.notna(first_valid_value):
                    # Ri-normalizza l'intera colonna per partire da 100
                    comparison_df[col] = (comparison_df[col] / first_valid_value) * self.base_value
                    # Assicura che il primo valore sia esattamente 100
                    comparison_df.loc[first_valid_idx, col] = self.base_value
        
        # Riempie i valori mancanti con forward fill (dopo la normalizzazione)
        comparison_df = comparison_df.ffill()
        
        # Assicura che alla data comune tutti i fondi disponibili abbiano valore 100
        if common_start_date in comparison_df.index:
            for col in comparison_df.columns:
                if pd.notna(comparison_df.loc[common_start_date, col]):
                    comparison_df.loc[common_start_date, col] = self.base_value
        
        return comparison_df
