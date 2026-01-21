"""
Classificazione automatica settori usando FinanceDatabase
"""

import warnings
from typing import Dict, Optional, List
import pandas as pd

try:
    # Prova prima con nome minuscolo (package installato)
    import financedatabase as fd
    FINANCEDATABASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        # Prova con nome maiuscolo
        import FinanceDatabase as fd
        FINANCEDATABASE_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        FINANCEDATABASE_AVAILABLE = False
        warnings.warn("FinanceDatabase non disponibile. Userà classificazione manuale.", UserWarning)


class SectorClassifier:
    """
    Classifica fondi/titoli in settori usando FinanceDatabase
    Con fallback a classificazione manuale se libreria non disponibile
    """
    
    def __init__(self):
        self.db = None
        if FINANCEDATABASE_AVAILABLE:
            try:
                self.db = fd
            except Exception as e:
                warnings.warn(f"Errore inizializzazione FinanceDatabase: {e}", UserWarning)
                self.db = None
    
    def get_sector_info(self, ticker: str, isin: str = None, exchange: str = None) -> Dict:
        """
        Recupera informazioni settore/industria per un ticker
        
        Args:
            ticker: Ticker del titolo (es. 'AAPL', 'AMZN')
            isin: ISIN (opzionale)
            exchange: Exchange code (opzionale, es. 'US', 'PA')
        
        Returns:
            {
                'sector': str,
                'industry': str,
                'market_cap': float,
                'country': str
            } o None se non trovato
        """
        if not self.db:
            return None
        
        try:
            # Prova a cercare per ticker
            # FinanceDatabase ha diverse funzioni per diversi tipi di asset
            # Prova prima con equities (azioni)
            try:
                equities = self.db.select_equities()
                if ticker in equities.index:
                    equity_info = equities.loc[ticker]
                    return {
                        'sector': equity_info.get('sector', ''),
                        'industry': equity_info.get('industry', ''),
                        'market_cap': equity_info.get('market_cap', None),
                        'country': equity_info.get('country', '')
                    }
            except Exception:
                pass
            
            # Prova con ETFs
            try:
                etfs = self.db.select_etfs()
                if ticker in etfs.index:
                    etf_info = etfs.loc[ticker]
                    return {
                        'sector': etf_info.get('category', ''),
                        'industry': '',
                        'market_cap': None,
                        'country': etf_info.get('country', '')
                    }
            except Exception:
                pass
            
            # Prova con funds
            try:
                funds = self.db.select_funds()
                if ticker in funds.index or (isin and isin in funds.index):
                    fund_info = funds.loc[ticker if ticker in funds.index else isin]
                    return {
                        'sector': fund_info.get('category', ''),
                        'industry': '',
                        'market_cap': None,
                        'country': fund_info.get('country', '')
                    }
            except Exception:
                pass
            
        except Exception as e:
            warnings.warn(f"Errore ricerca settore per {ticker}: {e}", UserWarning)
        
        return None
    
    def classify_fund(self, fund_data: Dict, ticker: str = None, isin: str = None) -> Optional[str]:
        """
        Classifica un fondo/titolo in un settore standardizzato
        
        Args:
            fund_data: Dizionario con dati del fondo
            ticker: Ticker (opzionale)
            isin: ISIN (opzionale)
        
        Returns:
            Nome settore standardizzato o None
        """
        # Prova con FinanceDatabase
        if self.db:
            sector_info = self.get_sector_info(
                ticker=ticker or fund_data.get('ticker', ''),
                isin=isin or fund_data.get('isin', '')
            )
            
            if sector_info and sector_info.get('sector'):
                sector = sector_info['sector']
                # Normalizza nome settore
                return self._normalize_sector_name(sector)
        
        # Fallback: usa logica esistente da data_processor
        return self._classify_manual(fund_data)
    
    def _normalize_sector_name(self, sector: str) -> str:
        """
        Normalizza nome settore a standard comune
        
        Args:
            sector: Nome settore da FinanceDatabase
        
        Returns:
            Nome settore normalizzato
        """
        if not sector:
            return None
        
        sector_lower = sector.lower()
        
        # Mappatura settori comuni
        sector_mapping = {
            'healthcare': 'Healthcare',
            'health care': 'Healthcare',
            'health sciences': 'Healthcare',
            'medical': 'Healthcare',
            'pharmaceuticals': 'Healthcare',
            'biotechnology': 'Healthcare',
            'technology': 'Technology',
            'tech': 'Technology',
            'information technology': 'Technology',
            'financial services': 'Finance',
            'financials': 'Finance',
            'finance': 'Finance',
            'consumer discretionary': 'Consumer',
            'consumer staples': 'Consumer',
            'consumer': 'Consumer',
            'energy': 'Energy',
            'industrials': 'Industrial',
            'industrial': 'Industrial',
            'materials': 'Materials',
            'real estate': 'Real Estate',
            'utilities': 'Utilities',
            'communication services': 'Communication',
            'telecommunications': 'Communication',
        }
        
        # Cerca match esatto o parziale
        for key, value in sector_mapping.items():
            if key in sector_lower:
                return value
        
        # Se non trovato, capitalizza prima lettera
        return sector.capitalize()
    
    def _classify_manual(self, fund_data: Dict) -> Optional[str]:
        """
        Classificazione manuale (fallback)
        Usa stessa logica di data_processor._determine_sector()
        """
        import config
        
        # Fonte 1: Da config.FUNDS
        fund_name = fund_data.get('name_short', '')
        fund_info = config.FUNDS.get(fund_name, {})
        if not fund_info:
            for key, value in config.FUNDS.items():
                if value.get('name_short') == fund_name:
                    fund_info = value
                    break
        
        if fund_info:
            category = fund_info.get('category', '')
            if category:
                if ' - ' in category:
                    return category.split(' - ')[-1]
                elif 'Healthcare' in category or 'Health' in category:
                    return 'Healthcare'
                elif 'Technology' in category or 'Tech' in category:
                    return 'Technology'
                elif 'Finance' in category or 'Financial' in category:
                    return 'Finance'
        
        # Fonte 2: Analisi nome
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
        
        return None
    
    def get_sector_peers(self, sector: str, country: str = None, limit: int = 50) -> List[str]:
        """
        Recupera lista di peer nello stesso settore
        
        Args:
            sector: Nome settore
            country: Codice paese (opzionale, es. 'US', 'FR')
            limit: Numero massimo di peer da restituire
        
        Returns:
            Lista di ticker di peer
        """
        if not self.db:
            return []
        
        try:
            equities = self.db.select_equities()
            if equities is None or equities.empty:
                return []
            
            # Filtra per settore
            sector_equities = equities[equities['sector'].str.contains(sector, case=False, na=False)]
            
            # Filtra per paese se specificato
            if country:
                sector_equities = sector_equities[sector_equities['country'].str.contains(country, case=False, na=False)]
            
            # Restituisci ticker (indice)
            peers = sector_equities.index.tolist()[:limit]
            return peers
            
        except Exception as e:
            warnings.warn(f"Errore recupero peer per settore {sector}: {e}", UserWarning)
            return []
