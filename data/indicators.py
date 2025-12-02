"""Technical indicators calculation for cryptocurrency analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import ta

import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for cryptocurrency trading analysis."""
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)."""
        try:
            return ta.momentum.rsi(close=data, window=period)
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_macd(
        data: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            macd_line = ta.trend.macd(close=data, window_fast=fast, window_slow=slow)
            macd_signal = ta.trend.macd_signal(close=data, window_fast=fast, window_slow=slow, window_sign=signal)
            macd_histogram = ta.trend.macd_diff(close=data, window_fast=fast, window_slow=slow, window_sign=signal)
            return {
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {
                'macd_line': pd.Series(index=data.index, dtype=float),
                'macd_signal': pd.Series(index=data.index, dtype=float),
                'macd_histogram': pd.Series(index=data.index, dtype=float)
            }
    
    @staticmethod
    def calculate_bollinger_bands(
        data: pd.Series, 
        period: int = 20, 
        std: float = 2
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        try:
            bb_upper = ta.volatility.bollinger_hband(close=data, window=period, window_dev=std)
            bb_lower = ta.volatility.bollinger_lband(close=data, window=period, window_dev=std)
            bb_middle = ta.trend.sma_indicator(close=data, window=period)
            bb_width = ta.volatility.bollinger_wband(close=data, window=period, window_dev=std)
            bb_percent = ta.volatility.bollinger_pband(close=data, window=period, window_dev=std)
            return {
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'bb_width': bb_width,
                'bb_percent': bb_percent
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {
                'bb_upper': pd.Series(index=data.index, dtype=float),
                'bb_middle': pd.Series(index=data.index, dtype=float),
                'bb_lower': pd.Series(index=data.index, dtype=float),
                'bb_width': pd.Series(index=data.index, dtype=float),
                'bb_percent': pd.Series(index=data.index, dtype=float)
            }
    
    @staticmethod
    def calculate_moving_averages(
        data: pd.Series, 
        periods: List[int] = [20, 50, 200]
    ) -> Dict[str, pd.Series]:
        """Calculate Simple and Exponential Moving Averages."""
        try:
            result = {}
            for period in periods:
                result[f'sma_{period}'] = ta.trend.sma_indicator(close=data, window=period)
                result[f'ema_{period}'] = ta.trend.ema_indicator(close=data, window=period)
            return result
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {}
    
    @staticmethod
    def calculate_stochastic(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series,
        k_period: int = 14, 
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        try:
            stoch_k = ta.momentum.stoch(high=high, low=low, close=close, window=k_period, smooth_window=d_period)
            stoch_d = ta.momentum.stoch_signal(high=high, low=low, close=close, window=k_period, smooth_window=d_period)
            return {
                'stoch_k': stoch_k,
                'stoch_d': stoch_d
            }
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return {
                'stoch_k': pd.Series(index=close.index, dtype=float),
                'stoch_d': pd.Series(index=close.index, dtype=float)
            }
    
    @staticmethod
    def calculate_atr(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range (ATR)."""
        try:
            return ta.volatility.average_true_range(high=high, low=low, close=close, window=period)
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    @staticmethod
    def calculate_support_resistance(
        data: pd.DataFrame, 
        lookback: int = 20
    ) -> Dict[str, List[float]]:
        """Calculate support and resistance levels."""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Find local maxima and minima
            resistance_levels = []
            support_levels = []
            
            for i in range(lookback, len(data) - lookback):
                # Check for resistance (local maximum)
                if high.iloc[i] == high.iloc[i-lookback:i+lookback+1].max():
                    resistance_levels.append(high.iloc[i])
                
                # Check for support (local minimum)
                if low.iloc[i] == low.iloc[i-lookback:i+lookback+1].min():
                    support_levels.append(low.iloc[i])
            
            # Remove duplicates and sort
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
            support_levels = sorted(list(set(support_levels)))
            
            # Keep only the most relevant levels (closest to current price)
            current_price = close.iloc[-1]
            
            # Filter resistance levels above current price
            resistance_levels = [r for r in resistance_levels if r > current_price][:3]
            
            # Filter support levels below current price
            support_levels = [s for s in support_levels if s < current_price][-3:]
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'resistance': [], 'support': []}
    
    @staticmethod
    def calculate_volume_indicators(
        close: pd.Series, 
        volume: pd.Series, 
        period: int = 20
    ) -> Dict[str, pd.Series]:
        """Calculate volume-based indicators."""
        try:
            # Volume SMA
            volume_sma = volume.rolling(window=period).mean()
            
            # Volume Rate of Change
            volume_roc = volume.pct_change(periods=period) * 100
            
            # On Balance Volume (OBV)
            obv = ta.volume.on_balance_volume(close=close, volume=volume)
            
            return {
                'volume_sma': volume_sma,
                'volume_roc': volume_roc,
                'obv': obv
            }
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            return {}
    
    @classmethod
    def calculate_all_indicators(
        cls, 
        data: pd.DataFrame,
        config: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Calculate all technical indicators for a given dataset."""
        if config is None:
            from config.settings import TECHNICAL_INDICATORS
            config = TECHNICAL_INDICATORS
        
        try:
            result_df = data.copy()
            
            # RSI
            rsi_config = config.get('rsi', {'period': 14})
            result_df['rsi'] = cls.calculate_rsi(data['close'], rsi_config['period'])
            
            # MACD
            macd_config = config.get('macd', {'fast': 12, 'slow': 26, 'signal': 9})
            macd_data = cls.calculate_macd(
                data['close'], 
                macd_config['fast'], 
                macd_config['slow'], 
                macd_config['signal']
            )
            for key, series in macd_data.items():
                result_df[key] = series
            
            # Bollinger Bands
            bb_config = config.get('bollinger', {'period': 20, 'std': 2})
            bb_data = cls.calculate_bollinger_bands(
                data['close'], 
                bb_config['period'], 
                bb_config['std']
            )
            for key, series in bb_data.items():
                result_df[key] = series
            
            # Moving Averages
            sma_periods = config.get('sma', {}).get('periods', [20, 50, 200])
            ma_data = cls.calculate_moving_averages(data['close'], sma_periods)
            for key, series in ma_data.items():
                result_df[key] = series
            
            # Stochastic
            stoch_config = config.get('stoch', {'k_period': 14, 'd_period': 3})
            stoch_data = cls.calculate_stochastic(
                data['high'], data['low'], data['close'],
                stoch_config['k_period'], stoch_config['d_period']
            )
            for key, series in stoch_data.items():
                result_df[key] = series
            
            # ATR
            atr_config = config.get('atr', {'period': 14})
            result_df['atr'] = cls.calculate_atr(
                data['high'], data['low'], data['close'], 
                atr_config['period']
            )
            
            # Volume indicators
            volume_data = cls.calculate_volume_indicators(data['close'], data['volume'])
            for key, series in volume_data.items():
                result_df[key] = series
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating all indicators: {e}")
            return data
    
    @staticmethod
    def get_signal_summary(data: pd.DataFrame) -> Dict[str, str]:
        """Generate trading signals summary from technical indicators."""
        try:
            signals = {}
            latest = data.iloc[-1]
            
            # RSI signals
            if 'rsi' in data.columns:
                rsi = latest['rsi']
                if rsi > 70:
                    signals['rsi'] = 'overbought'
                elif rsi < 30:
                    signals['rsi'] = 'oversold'
                else:
                    signals['rsi'] = 'neutral'
            
            # MACD signals
            if 'macd_line' in data.columns and 'macd_signal' in data.columns:
                macd_line = latest['macd_line']
                macd_signal = latest['macd_signal']
                if macd_line > macd_signal:
                    signals['macd'] = 'bullish'
                else:
                    signals['macd'] = 'bearish'
            
            # Bollinger Bands signals
            if all(col in data.columns for col in ['bb_upper', 'bb_lower', 'close']):
                price = latest['close']
                bb_upper = latest['bb_upper']
                bb_lower = latest['bb_lower']
                
                if price > bb_upper:
                    signals['bollinger'] = 'overbought'
                elif price < bb_lower:
                    signals['bollinger'] = 'oversold'
                else:
                    signals['bollinger'] = 'neutral'
            
            # Moving Average signals
            if 'sma_20' in data.columns and 'sma_50' in data.columns:
                sma_20 = latest['sma_20']
                sma_50 = latest['sma_50']
                price = latest['close']
                
                if price > sma_20 > sma_50:
                    signals['trend'] = 'strong_bullish'
                elif price > sma_20:
                    signals['trend'] = 'bullish'
                elif price < sma_20 < sma_50:
                    signals['trend'] = 'strong_bearish'
                else:
                    signals['trend'] = 'bearish'
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signal summary: {e}")
            return {}
