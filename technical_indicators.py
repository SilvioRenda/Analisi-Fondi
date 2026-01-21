"""
Indicatori tecnici usando pandas-ta
"""

import warnings
from typing import Dict, Optional
import pandas as pd
import numpy as np

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    warnings.warn("pandas-ta non disponibile. Indicatori tecnici non disponibili.", UserWarning)


class TechnicalIndicators:
    """
    Calcola indicatori tecnici usando pandas-ta
    Con fallback a calcoli manuali se libreria non disponibile
    """
    
    def __init__(self):
        self.available = PANDAS_TA_AVAILABLE
    
    def calculate_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calcola indicatori tecnici standard
        
        Args:
            price_data: DataFrame con colonne 'Price' o 'Close' e indice DatetimeIndex
        
        Returns:
            DataFrame con colonne aggiuntive:
            - RSI (Relative Strength Index)
            - MACD, MACD_signal, MACD_hist (Moving Average Convergence Divergence)
            - BB_upper, BB_middle, BB_lower (Bollinger Bands)
            - SMA_20, SMA_50, SMA_200 (Simple Moving Averages)
            - EMA_12, EMA_26 (Exponential Moving Averages)
        """
        if price_data is None or price_data.empty:
            return price_data
        
        # Identifica colonna prezzo
        price_col = None
        if 'Price' in price_data.columns:
            price_col = 'Price'
        elif 'Close' in price_data.columns:
            price_col = 'Close'
        elif 'Adj Close' in price_data.columns:
            price_col = 'Adj Close'
        else:
            # Usa prima colonna numerica
            numeric_cols = price_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                price_col = numeric_cols[0]
            else:
                return price_data
        
        result = price_data.copy()
        prices = result[price_col]
        
        if self.available:
            # Usa pandas-ta
            try:
                # RSI (Relative Strength Index)
                rsi = ta.rsi(prices, length=14)
                if rsi is not None:
                    result['RSI'] = rsi
                
                # MACD
                macd = ta.macd(prices, fast=12, slow=26, signal=9)
                if macd is not None:
                    if isinstance(macd, pd.DataFrame):
                        result = pd.concat([result, macd], axis=1)
                    else:
                        result['MACD'] = macd
                
                # Bollinger Bands
                bb = ta.bbands(prices, length=20, std=2)
                if bb is not None:
                    if isinstance(bb, pd.DataFrame):
                        result = pd.concat([result, bb], axis=1)
                    else:
                        result['BB_upper'] = bb
                
                # Simple Moving Averages
                sma_20 = ta.sma(prices, length=20)
                sma_50 = ta.sma(prices, length=50)
                sma_200 = ta.sma(prices, length=200)
                
                if sma_20 is not None:
                    result['SMA_20'] = sma_20
                if sma_50 is not None:
                    result['SMA_50'] = sma_50
                if sma_200 is not None:
                    result['SMA_200'] = sma_200
                
                # Exponential Moving Averages
                ema_12 = ta.ema(prices, length=12)
                ema_26 = ta.ema(prices, length=26)
                
                if ema_12 is not None:
                    result['EMA_12'] = ema_12
                if ema_26 is not None:
                    result['EMA_26'] = ema_26
                
            except Exception as e:
                warnings.warn(f"Errore calcolo indicatori con pandas-ta: {e}", UserWarning)
                # Fallback a calcoli manuali
                result = self._calculate_indicators_manual(result, prices)
        else:
            # Calcoli manuali
            result = self._calculate_indicators_manual(result, prices)
        
        return result
    
    def _calculate_indicators_manual(self, df: pd.DataFrame, prices: pd.Series) -> pd.DataFrame:
        """
        Calcola indicatori tecnici manualmente (fallback)
        """
        result = df.copy()
        
        # RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        
        # SMA
        result['SMA_20'] = prices.rolling(window=20).mean()
        result['SMA_50'] = prices.rolling(window=50).mean()
        result['SMA_200'] = prices.rolling(window=200).mean()
        
        # EMA
        result['EMA_12'] = prices.ewm(span=12, adjust=False).mean()
        result['EMA_26'] = prices.ewm(span=26, adjust=False).mean()
        
        # MACD
        result['MACD'] = result['EMA_12'] - result['EMA_26']
        result['MACD_signal'] = result['MACD'].ewm(span=9, adjust=False).mean()
        result['MACD_hist'] = result['MACD'] - result['MACD_signal']
        
        # Bollinger Bands
        sma_20 = result['SMA_20']
        std_20 = prices.rolling(window=20).std()
        result['BB_middle'] = sma_20
        result['BB_upper'] = sma_20 + (std_20 * 2)
        result['BB_lower'] = sma_20 - (std_20 * 2)
        
        return result
    
    def generate_signals(self, indicators_df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera segnali di trading basati su indicatori
        
        Args:
            indicators_df: DataFrame con indicatori calcolati
        
        Returns:
            DataFrame con colonne aggiuntive:
            - buy_signal: bool
            - sell_signal: bool
            - signal_strength: float (0-100)
        """
        if indicators_df is None or indicators_df.empty:
            return indicators_df
        
        result = indicators_df.copy()
        
        # Inizializza colonne segnali
        result['buy_signal'] = False
        result['sell_signal'] = False
        result['signal_strength'] = 0.0
        
        # Identifica colonna prezzo
        price_col = None
        for col in ['Price', 'Close', 'Adj Close']:
            if col in result.columns:
                price_col = col
                break
        
        if price_col is None:
            return result
        
        prices = result[price_col]
        
        # Segnali basati su RSI
        if 'RSI' in result.columns:
            rsi = result['RSI']
            # Oversold (RSI < 30) -> Buy signal
            result.loc[rsi < 30, 'buy_signal'] = True
            # Overbought (RSI > 70) -> Sell signal
            result.loc[rsi > 70, 'sell_signal'] = True
        
        # Segnali basati su MACD
        if 'MACD' in result.columns and 'MACD_signal' in result.columns:
            macd = result['MACD']
            macd_signal = result['MACD_signal']
            # MACD crossover sopra signal -> Buy
            result.loc[(macd > macd_signal) & (macd.shift(1) <= macd_signal.shift(1)), 'buy_signal'] = True
            # MACD crossover sotto signal -> Sell
            result.loc[(macd < macd_signal) & (macd.shift(1) >= macd_signal.shift(1)), 'sell_signal'] = True
        
        # Segnali basati su Bollinger Bands
        if 'BB_lower' in result.columns and 'BB_upper' in result.columns:
            bb_lower = result['BB_lower']
            bb_upper = result['BB_upper']
            # Prezzo tocca banda inferiore -> Buy
            result.loc[prices <= bb_lower, 'buy_signal'] = True
            # Prezzo tocca banda superiore -> Sell
            result.loc[prices >= bb_upper, 'sell_signal'] = True
        
        # Segnali basati su Moving Averages
        if 'SMA_20' in result.columns and 'SMA_50' in result.columns:
            sma_20 = result['SMA_20']
            sma_50 = result['SMA_50']
            # Golden Cross (SMA_20 > SMA_50) -> Buy
            result.loc[(sma_20 > sma_50) & (sma_20.shift(1) <= sma_50.shift(1)), 'buy_signal'] = True
            # Death Cross (SMA_20 < SMA_50) -> Sell
            result.loc[(sma_20 < sma_50) & (sma_20.shift(1) >= sma_50.shift(1)), 'sell_signal'] = True
        
        # Calcola signal strength (numero di indicatori che confermano)
        buy_count = result['buy_signal'].astype(int)
        sell_count = result['sell_signal'].astype(int)
        
        # Signal strength: differenza tra buy e sell signals
        result['signal_strength'] = (buy_count - sell_count) * 25  # Scala 0-100
        
        return result
