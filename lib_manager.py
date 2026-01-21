"""
Gestore centralizzato per librerie esterne con fallback automatico
"""

import warnings
from typing import Optional, Dict, Any

class LibraryManager:
    """
    Gestisce disponibilità e utilizzo di librerie esterne
    Fornisce fallback automatico se librerie non disponibili
    """
    
    def __init__(self):
        self.financetoolkit_available = False
        self.financedatabase_available = False
        self.riskfolio_available = False
        self.pandas_ta_available = False
        self.polars_available = False
        
        self._check_availability()
    
    def _check_availability(self):
        """Verifica disponibilità di tutte le librerie"""
        # Verifica FinanceToolkit
        try:
            import financetoolkit
            self.financetoolkit_available = True
        except ImportError:
            warnings.warn("FinanceToolkit non disponibile. Userà calcolo Beta manuale.", UserWarning)
        
        # Verifica FinanceDatabase
        try:
            import financedatabase
            self.financedatabase_available = True
        except (ImportError, ModuleNotFoundError):
            try:
                import FinanceDatabase
                self.financedatabase_available = True
            except (ImportError, ModuleNotFoundError):
                warnings.warn("FinanceDatabase non disponibile. Userà classificazione settori manuale.", UserWarning)
        
        # Verifica Riskfolio-Lib
        try:
            import riskfolio as rp
            self.riskfolio_available = True
        except ImportError:
            warnings.warn("Riskfolio-Lib non disponibile. Analisi portfolio limitata.", UserWarning)
        
        # Verifica pandas-ta
        try:
            import pandas_ta as ta
            self.pandas_ta_available = True
        except ImportError:
            warnings.warn("pandas-ta non disponibile. Indicatori tecnici non disponibili.", UserWarning)
        
        # Verifica Polars
        try:
            import polars as pl
            self.polars_available = True
        except ImportError:
            # Polars è opzionale, non serve warning
            pass
    
    def get_metric_calculator(self):
        """
        Restituisce calculator disponibile (avanzato o base)
        
        Returns:
            AdvancedMetricsCalculator se disponibile, altrimenti None
        """
        if self.financetoolkit_available:
            try:
                from advanced_metrics import AdvancedMetricsCalculator
                return AdvancedMetricsCalculator()
            except ImportError:
                pass
        return None
    
    def get_sector_classifier(self):
        """
        Restituisce classifier disponibile (avanzato o base)
        
        Returns:
            SectorClassifier se disponibile, altrimenti None
        """
        if self.financedatabase_available:
            try:
                from sector_classifier import SectorClassifier
                return SectorClassifier()
            except ImportError:
                pass
        return None
    
    def get_portfolio_analyzer(self):
        """
        Restituisce portfolio analyzer disponibile
        
        Returns:
            PortfolioAnalyzer se disponibile, altrimenti None
        """
        if self.riskfolio_available:
            try:
                from portfolio_analyzer import PortfolioAnalyzer
                return PortfolioAnalyzer()
            except ImportError:
                pass
        return None
    
    def get_technical_indicators(self):
        """
        Restituisce technical indicators calculator disponibile
        
        Returns:
            TechnicalIndicators se disponibile, altrimenti None
        """
        if self.pandas_ta_available:
            try:
                from technical_indicators import TechnicalIndicators
                return TechnicalIndicators()
            except ImportError:
                pass
        return None
    
    def is_available(self, library_name: str) -> bool:
        """
        Verifica se una libreria specifica è disponibile
        
        Args:
            library_name: Nome libreria ('financetoolkit', 'financedatabase', etc.)
        
        Returns:
            True se disponibile, False altrimenti
        """
        library_map = {
            'financetoolkit': self.financetoolkit_available,
            'financedatabase': self.financedatabase_available,
            'riskfolio': self.riskfolio_available,
            'pandas_ta': self.pandas_ta_available,
            'polars': self.polars_available
        }
        return library_map.get(library_name.lower(), False)
    
    def get_status(self) -> Dict[str, bool]:
        """
        Restituisce stato di tutte le librerie
        
        Returns:
            Dizionario con stato di ogni libreria
        """
        return {
            'financetoolkit': self.financetoolkit_available,
            'financedatabase': self.financedatabase_available,
            'riskfolio': self.riskfolio_available,
            'pandas_ta': self.pandas_ta_available,
            'polars': self.polars_available
        }
