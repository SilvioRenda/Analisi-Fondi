"""
Metriche avanzate usando FinanceToolkit
"""

import warnings
from typing import Dict, Optional
import pandas as pd
import numpy as np

try:
    from financetoolkit import Toolkit
    FINANCETOOLKIT_AVAILABLE = True
except ImportError:
    FINANCETOOLKIT_AVAILABLE = False
    warnings.warn("FinanceToolkit non disponibile. Userà calcolo metriche manuale.", UserWarning)


class AdvancedMetricsCalculator:
    """
    Calcola metriche avanzate usando FinanceToolkit
    Con fallback a calcolo manuale se libreria non disponibile
    """
    
    def __init__(self, api_key: str = None):
        self.toolkit = None
        self.api_key = api_key
        # FinanceToolkit richiede tickers nell'inizializzazione
        # Lo inizializzeremo quando necessario con tickers specifici
    
    def calculate_beta_advanced(self, ticker: str, benchmark: str, 
                                period: str = 'yearly') -> Optional[Dict]:
        """
        Calcola Beta usando FinanceToolkit (più robusto)
        
        Args:
            ticker: Ticker del titolo/fondo
            benchmark: Ticker del benchmark (es. 'SPY', 'EZU')
            period: Periodo ('yearly', 'quarterly', 'monthly', 'daily')
        
        Returns:
            {
                'beta': float,
                'alpha': float,
                'correlation': float,
                'r_squared': float
            } o None se non disponibile
        """
        if not FINANCETOOLKIT_AVAILABLE:
            return None
        
        try:
            # FinanceToolkit richiede tickers nell'inizializzazione
            toolkit = Toolkit(tickers=[ticker, benchmark], api_key=self.api_key)
            
            # Calcola Beta
            beta_df = toolkit.ratios.get_beta(period=period)
            
            if beta_df is not None and not beta_df.empty and ticker in beta_df.index:
                beta_value = beta_df.loc[ticker, benchmark] if benchmark in beta_df.columns else None
                
                if beta_value is not None and not pd.isna(beta_value):
                    return {
                        'beta': float(beta_value),
                        'alpha': None,  # Da calcolare separatamente se necessario
                        'correlation': None,  # Da calcolare separatamente se necessario
                        'r_squared': None  # Da calcolare separatamente se necessario
                    }
        except Exception as e:
            warnings.warn(f"Errore calcolo Beta avanzato per {ticker}: {e}", UserWarning)
        
        return None
    
    def calculate_risk_metrics(self, ticker: str, risk_free_rate: float = 0.0) -> Optional[Dict]:
        """
        Calcola metriche di rischio avanzate
        
        Args:
            ticker: Ticker del titolo/fondo
            risk_free_rate: Tasso risk-free (default: 0.0)
        
        Returns:
            {
                'sharpe_ratio': float,
                'sortino_ratio': float,
                'treynor_ratio': float,
                'information_ratio': float,
                'max_drawdown': float
            } o None se non disponibile
        """
        if not FINANCETOOLKIT_AVAILABLE:
            return None
        
        try:
            # FinanceToolkit richiede tickers nell'inizializzazione
            toolkit = Toolkit(tickers=[ticker], api_key=self.api_key)
            metrics = {}
            
            # Sharpe Ratio
            try:
                sharpe = toolkit.ratios.get_sharpe_ratio(period='yearly')
                if sharpe is not None and not sharpe.empty and ticker in sharpe.index:
                    sharpe_value = sharpe.loc[ticker].iloc[-1] if len(sharpe.loc[ticker].shape) > 0 else sharpe.loc[ticker]
                    if pd.notna(sharpe_value):
                        metrics['sharpe_ratio'] = float(sharpe_value)
            except Exception:
                pass
            
            # Sortino Ratio
            try:
                sortino = toolkit.ratios.get_sortino_ratio(period='yearly')
                if sortino is not None and not sortino.empty and ticker in sortino.index:
                    sortino_value = sortino.loc[ticker].iloc[-1] if len(sortino.loc[ticker].shape) > 0 else sortino.loc[ticker]
                    if pd.notna(sortino_value):
                        metrics['sortino_ratio'] = float(sortino_value)
            except Exception:
                pass
            
            # Treynor Ratio (richiede Beta)
            try:
                treynor = toolkit.ratios.get_treynor_ratio(period='yearly')
                if treynor is not None and not treynor.empty and ticker in treynor.index:
                    treynor_value = treynor.loc[ticker].iloc[-1] if len(treynor.loc[ticker].shape) > 0 else treynor.loc[ticker]
                    if pd.notna(treynor_value):
                        metrics['treynor_ratio'] = float(treynor_value)
            except Exception:
                pass
            
            # Max Drawdown
            try:
                drawdown = toolkit.technicals.get_max_drawdown(period='yearly')
                if drawdown is not None and not drawdown.empty and ticker in drawdown.index:
                    drawdown_value = drawdown.loc[ticker].iloc[-1] if len(drawdown.loc[ticker].shape) > 0 else drawdown.loc[ticker]
                    if pd.notna(drawdown_value):
                        metrics['max_drawdown'] = float(drawdown_value)
            except Exception:
                pass
            
            return metrics if metrics else None
            
        except Exception as e:
            warnings.warn(f"Errore calcolo metriche rischio per {ticker}: {e}", UserWarning)
            return None
    
    def calculate_capm_metrics(self, ticker: str, benchmark: str, 
                             risk_free_rate: float = 0.0) -> Optional[Dict]:
        """
        Calcola metriche CAPM
        
        Args:
            ticker: Ticker del titolo/fondo
            benchmark: Ticker del benchmark
            risk_free_rate: Tasso risk-free
        
        Returns:
            {
                'expected_return': float,  # Expected Return (CAPM)
                'beta': float,
                'alpha': float,
                'risk_premium': float
            } o None se non disponibile
        """
        if not FINANCETOOLKIT_AVAILABLE:
            return None
        
        try:
            # Calcola Beta
            beta_result = self.calculate_beta_advanced(ticker, benchmark)
            if not beta_result or beta_result.get('beta') is None:
                return None
            
            beta = beta_result['beta']
            
            # Calcola returns usando FinanceToolkit
            try:
                toolkit = Toolkit(tickers=[benchmark], api_key=self.api_key)
                historical = toolkit.get_historical_data(period='yearly')
                if historical is not None and not historical.empty and benchmark in historical.columns:
                    # Calcola return medio annuale del benchmark
                    benchmark_prices = historical[benchmark]
                    benchmark_returns = benchmark_prices.pct_change().dropna()
                    market_return = benchmark_returns.mean() * 252  # Annualizzato
                    
                    expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
                    risk_premium = beta * (market_return - risk_free_rate)
                    
                    return {
                        'expected_return': expected_return,
                        'beta': beta,
                        'alpha': None,  # Da calcolare con returns effettivi
                        'risk_premium': risk_premium
                    }
            except Exception:
                pass
            
        except Exception as e:
            warnings.warn(f"Errore calcolo CAPM per {ticker}: {e}", UserWarning)
        
        return None
    
    def calculate_from_data(self, returns: pd.Series, benchmark_returns: pd.Series = None,
                           risk_free_rate: float = 0.0) -> Dict:
        """
        Calcola metriche avanzate da dati raw (returns)
        Utile quando FinanceToolkit non è disponibile o per dati custom
        
        Args:
            returns: Serie con returns del titolo/fondo
            benchmark_returns: Serie con returns del benchmark (opzionale)
            risk_free_rate: Tasso risk-free
        
        Returns:
            Dizionario con metriche calcolate
        """
        metrics = {}
        
        if returns is None or returns.empty:
            return metrics
        
        # Sharpe Ratio
        if len(returns) > 0:
            mean_return = returns.mean()
            std_return = returns.std()
            if std_return > 0:
                metrics['sharpe_ratio'] = (mean_return - risk_free_rate) / std_return
        
        # Sortino Ratio (usa solo downside deviation)
        if len(returns) > 0:
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = downside_returns.std()
                if downside_std > 0:
                    metrics['sortino_ratio'] = (mean_return - risk_free_rate) / downside_std
        
        # Max Drawdown
        if len(returns) > 0:
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            metrics['max_drawdown'] = drawdown.min()
        
        # Beta e Alpha (se benchmark disponibile)
        if benchmark_returns is not None and not benchmark_returns.empty:
            # Allinea serie
            aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
            
            if len(aligned_returns) > 0:
                # Beta
                covariance = aligned_returns.cov(aligned_benchmark)
                variance = aligned_benchmark.var()
                if variance > 0:
                    metrics['beta'] = covariance / variance
                    
                    # Alpha
                    mean_benchmark = aligned_benchmark.mean()
                    metrics['alpha'] = mean_return - (risk_free_rate + metrics['beta'] * (mean_benchmark - risk_free_rate))
        
        return metrics
