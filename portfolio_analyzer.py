"""
Analisi portfolio avanzata usando Riskfolio-Lib
"""

import warnings
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

try:
    import riskfolio as rp
    RISKFOLIO_AVAILABLE = True
except ImportError:
    RISKFOLIO_AVAILABLE = False
    warnings.warn("Riskfolio-Lib non disponibile. Analisi portfolio limitata.", UserWarning)


class PortfolioAnalyzer:
    """
    Analizza portfolio usando Riskfolio-Lib
    Con fallback a calcoli manuali se libreria non disponibile
    """
    
    def __init__(self):
        self.available = RISKFOLIO_AVAILABLE
    
    def calculate_portfolio_metrics(self, returns_df: pd.DataFrame, 
                                     weights: Dict = None) -> Dict:
        """
        Calcola metriche portfolio aggregate
        
        Args:
            returns_df: DataFrame con returns di tutti i fondi/titoli (colonne = fondi, righe = date)
            weights: Dizionario pesi {fund_name: weight} (opzionale, default: equal weight)
        
        Returns:
            {
                'portfolio_return': float,
                'portfolio_volatility': float,
                'portfolio_sharpe': float,
                'portfolio_beta': float,
                'diversification_ratio': float
            }
        """
        if returns_df is None or returns_df.empty:
            return {}
        
        # Calcola pesi (equal weight se non specificati)
        if weights is None:
            n_assets = len(returns_df.columns)
            weights = {col: 1.0 / n_assets for col in returns_df.columns}
        
        # Normalizza pesi (somma = 1)
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Crea array pesi in ordine colonne
        weight_array = np.array([weights.get(col, 0.0) for col in returns_df.columns])
        
        # Calcola returns portfolio (weighted average)
        portfolio_returns = (returns_df * weight_array).sum(axis=1)
        
        # Metriche base
        portfolio_return = portfolio_returns.mean() * 252  # Annualizzato
        portfolio_volatility = portfolio_returns.std() * np.sqrt(252)  # Annualizzato
        
        # Sharpe Ratio (assumendo risk-free = 0)
        portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Diversification Ratio
        # = (weighted average volatility) / (portfolio volatility)
        individual_vols = returns_df.std() * np.sqrt(252)
        weighted_avg_vol = (individual_vols * weight_array).sum()
        diversification_ratio = weighted_avg_vol / portfolio_volatility if portfolio_volatility > 0 else 1.0
        
        metrics = {
            'portfolio_return': round(portfolio_return * 100, 2),  # In percentuale
            'portfolio_volatility': round(portfolio_volatility * 100, 2),  # In percentuale
            'portfolio_sharpe': round(portfolio_sharpe, 2),
            'diversification_ratio': round(diversification_ratio, 2)
        }
        
        # Usa Riskfolio-Lib per metriche avanzate se disponibile
        if self.available:
            try:
                # Riskfolio richiede formato specifico
                # Per ora usiamo calcoli manuali sopra
                # In futuro possiamo integrare funzionalità avanzate di Riskfolio
                pass
            except Exception:
                pass
        
        return metrics
    
    def sector_allocation_analysis(self, processed_data: Dict) -> Dict:
        """
        Analizza allocazione settoriale del portfolio
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
        
        Returns:
            {
                'sector_weights': Dict,  # {sector: weight}
                'sector_returns': Dict,  # {sector: return}
                'sector_volatilities': Dict,  # {sector: volatility}
                'concentration_risk': float  # Herfindahl-Hirschman Index
            }
        """
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        sectors = processor.group_by_sector(processed_data)
        
        sector_weights = {}
        sector_returns = {}
        sector_volatilities = {}
        
        # Calcola pesi e metriche per settore
        total_funds = len(processed_data)
        
        for sector, fund_names in sectors.items():
            sector_weight = len(fund_names) / total_funds if total_funds > 0 else 0
            sector_weights[sector] = round(sector_weight * 100, 2)  # In percentuale
            
            # Calcola return medio settore
            sector_returns_list = []
            sector_vols_list = []
            
            for fund_name in fund_names:
                if fund_name in processed_data:
                    fund_data = processed_data[fund_name]
                    metrics = fund_data.get('metrics', {})
                    
                    if metrics.get('annualized_return') is not None:
                        sector_returns_list.append(metrics['annualized_return'])
                    if metrics.get('volatility') is not None:
                        sector_vols_list.append(metrics['volatility'])
            
            if sector_returns_list:
                sector_returns[sector] = round(np.mean(sector_returns_list), 2)
            if sector_vols_list:
                sector_volatilities[sector] = round(np.mean(sector_vols_list), 2)
        
        # Calcola Concentration Risk (HHI)
        weights_list = list(sector_weights.values())
        if weights_list:
            # Normalizza pesi (somma = 1)
            total_weight = sum(weights_list)
            if total_weight > 0:
                normalized_weights = [w / total_weight for w in weights_list]
                hhi = sum(w ** 2 for w in normalized_weights) * 10000  # HHI in scala 0-10000
            else:
                hhi = 0
        else:
            hhi = 0
        
        return {
            'sector_weights': sector_weights,
            'sector_returns': sector_returns,
            'sector_volatilities': sector_volatilities,
            'concentration_risk': round(hhi, 2)  # HHI: 0 = perfettamente diversificato, 10000 = concentrato
        }
    
    def optimize_portfolio(self, returns_df: pd.DataFrame, 
                          method: str = 'max_sharpe',
                          risk_free_rate: float = 0.0) -> Optional[Dict]:
        """
        Ottimizza allocazione portfolio
        
        Args:
            returns_df: DataFrame con returns
            method: Metodo ottimizzazione ('max_sharpe', 'min_volatility', 'efficient_risk', 'efficient_return')
            risk_free_rate: Tasso risk-free
        
        Returns:
            {
                'optimal_weights': Dict,  # {fund_name: optimal_weight}
                'expected_return': float,
                'expected_volatility': float,
                'sharpe_ratio': float
            } o None se non disponibile
        """
        if not self.available or returns_df is None or returns_df.empty:
            return None
        
        try:
            # Prepara dati per Riskfolio
            # Riskfolio richiede formato specifico
            # Per semplicità, usiamo calcolo manuale base
            
            # Calcola matrice covarianza
            cov_matrix = returns_df.cov() * 252  # Annualizzata
            
            # Calcola returns attesi (media annualizzata)
            expected_returns = returns_df.mean() * 252
            
            # Ottimizzazione base: Max Sharpe
            if method == 'max_sharpe':
                # Risolvi: max (w^T * mu - rf) / sqrt(w^T * Sigma * w)
                # Soggetto a: sum(w) = 1, w >= 0
                
                from scipy.optimize import minimize
                
                n_assets = len(returns_df.columns)
                
                def negative_sharpe(weights):
                    portfolio_return = np.dot(weights, expected_returns)
                    portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                    if portfolio_vol > 0:
                        sharpe = (portfolio_return - risk_free_rate) / portfolio_vol
                        return -sharpe  # Negativo perché minimizziamo
                    return 1e10
                
                # Vincoli
                constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
                bounds = tuple((0, 1) for _ in range(n_assets))
                
                # Punto iniziale (equal weight)
                initial_weights = np.array([1.0 / n_assets] * n_assets)
                
                # Ottimizza
                result = minimize(negative_sharpe, initial_weights, method='SLSQP',
                                bounds=bounds, constraints=constraints)
                
                if result.success:
                    optimal_weights = result.x
                    optimal_weights_dict = {
                        returns_df.columns[i]: round(optimal_weights[i] * 100, 2)
                        for i in range(n_assets)
                    }
                    
                    # Calcola metriche portfolio ottimizzato
                    portfolio_return = np.dot(optimal_weights, expected_returns) * 100
                    portfolio_vol = np.sqrt(np.dot(optimal_weights, np.dot(cov_matrix, optimal_weights))) * 100
                    sharpe = (portfolio_return / 100 - risk_free_rate) / (portfolio_vol / 100) if portfolio_vol > 0 else 0
                    
                    return {
                        'optimal_weights': optimal_weights_dict,
                        'expected_return': round(portfolio_return, 2),
                        'expected_volatility': round(portfolio_vol, 2),
                        'sharpe_ratio': round(sharpe, 2)
                    }
            
        except Exception as e:
            warnings.warn(f"Errore ottimizzazione portfolio: {e}", UserWarning)
        
        return None
